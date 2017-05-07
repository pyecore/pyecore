"""
This module is the heart of PyEcore. It defines all the basic concepts that
are common to EMF-Java and PyEcore (EObject/EClass...).

These concepts are enough if dynamic metamodel instance are handled (code
generation is not required).
"""
from functools import partial
import sys
import keyword
import inspect
from ordered_set import OrderedSet, is_iterable
from .notification import ENotifer, Notification, Kind, EObserver


name = 'ecore'
nsPrefix = 'ecore'
nsURI = 'http://www.eclipse.org/emf/2002/Ecore'

# This var will be automatically populated.
# In this case, it MUST be set to an empty dict,
# otherwise, the getEClassifier would be overriden
eClassifiers = {}  # Will be automatically populated
eSubpackages = []


def default_eURIFragment():
    return '/'


def eURIFragment():
    return '#/'


def getEClassifier(name, searchspace=None):
    searchspace = searchspace or eClassifiers
    try:
        return searchspace[name]
    except KeyError:
        return None


class BadValueError(TypeError):
    def __init__(self, got=None, expected=None):
        msg = "Expected type {0}, but got type {1} with value {2} instead"
        msg = msg.format(expected, type(got).__name__, got)
        super().__init__(msg)


class EcoreUtils(object):
    def isinstance(obj, _type):
        if obj is None:
            return True
        elif isinstance(obj, EProxy) and not obj._resolved:
            return True
        elif _type is EPackage:
            return isinstance(obj, _type) or \
                       inspect.ismodule(obj) and hasattr(obj, 'nsURI')
        elif _type is EClassifier:
            return obj is _type or isinstance(obj, _type) or \
                        hasattr(obj, '_staticEClass') and obj._staticEClass
        elif isinstance(_type, EEnum):
            return obj in _type
        elif isinstance(_type, (EDataType, EAttribute)):
            return isinstance(obj, _type.eType)
        elif isinstance(_type, EClass):
            if isinstance(obj, EObject):
                return isinstance(obj, _type.python_class)
                # return obj.eClass is _type \
                #        or _type in obj.eClass.eAllSuperTypes()
            return False
        return isinstance(obj, _type) or obj is _type.eClass

    def getRoot(obj):
        if not obj:
            return None
        previous = obj
        while previous.eContainer() is not None:
            previous = previous.eContainer()
        return previous


class Core(object):
    def _promote(cls, abstract=False):
        cls.eClass = EClass(cls.__name__, metainstance=cls)
        cls.eClass.abstract = abstract
        cls._staticEClass = True
        # init super types
        for _cls in cls.__bases__:
            if _cls is not EObject:
                cls.eClass.eSuperTypes.append(_cls.eClass)
        # init eclass by reflection
        for k, feature in cls.__dict__.items():
            if isinstance(feature, EStructuralFeature):
                if not feature.name:
                    feature.name = k
                cls.eClass.eStructuralFeatures.append(feature)
            elif inspect.isfunction(feature):
                if k == '__init__':
                    continue
                argspect = inspect.getargspec(feature)
                args = argspect.args
                if len(args) < 1 or args[0] != 'self':
                    continue
                operation = EOperation(feature.__name__)
                defaults = argspect.defaults
                len_defaults = len(defaults) if defaults else 0
                nb_required = len(args) - len_defaults
                for i, parameter_name in enumerate(args):
                    parameter = EParameter(parameter_name, eType=ENativeType)
                    if i < nb_required:
                        parameter.required = True
                    operation.eParameters.append(parameter)
                cls.eClass.eOperations.append(operation)

    def register_classifier(cls, abstract=False, promote=False):
        if promote:
            Core._promote(cls, abstract)
        epackage = sys.modules[cls.__module__]
        if not hasattr(epackage, 'eClassifiers'):
            eclassifs = {}
            epackage.eClassifiers = eclassifs
            epackage.getEClassifier = partial(getEClassifier,
                                              searchspace=eclassifs)
        object.__setattr__(cls.eClass, 'ePackage', epackage)
        cname = cls.name if isinstance(cls, EClassifier) else cls.__name__
        epackage.eClassifiers[cname] = cls
        if hasattr(epackage, 'eResource'):
            cls._eresource = epackage.eResource
        if isinstance(cls, EDataType):
            cls._container = epackage
        else:
            cls.eClass._container = epackage


class EObject(ENotifer):
    _staticEClass = True

    def __init__(self):
        self.__subinit__()
        self.__initmetattr__()
        self._isready = True

    def __subinit__(self):
        self._xmiid = None
        self._isset = set()
        self._container = None
        self._isready = False
        self._containment_feature = None
        self._eresource = None
        self.listeners = []
        self._eternal_listener = []
        self._inverse_rels = set()

    def __initmetattr__(self, _super=None):
        _super = _super or self.__class__
        if _super is EObject:
            return
        for super_class in _super.__bases__:
            super_class.__initmetattr__(self, super_class)
        for key, feature in _super.__dict__.items():
            if not isinstance(feature, EStructuralFeature):
                continue
            if feature.many:
                object.__setattr__(self,
                                   key,
                                   ECollection.create(self, feature))
            else:
                default_value = None
                if isinstance(feature, EAttribute):
                    default_value = feature.eType.default_value
                object.__setattr__(self, key, default_value)

    def eContainer(self):
        return self._container

    def eContainmentFeature(self):
        return self._containment_feature

    def eIsSet(self, feature):
        if isinstance(feature, str):
            feature = self.eClass.findEStructuralFeature(feature)
        return feature in self._isset

    @property
    def eResource(self):
        return self._eresource

    def eGet(self, feature):
        if isinstance(feature, str):
            return self.__getattribute__(feature)
        elif isinstance(feature, EStructuralFeature):
            return self.__getattribute__(feature.name)
        raise TypeError('Feature must have str or EStructuralFeature type')

    def eSet(self, feature, value):
        if isinstance(feature, str):
            self.__setattr__(feature, value)
        elif isinstance(feature, EStructuralFeature):
            self.__setattr__(feature.name, value)
        else:
            raise TypeError('Feature must have str or '
                            'EStructuralFeature type')

    def delete(self, recursive=True):
        if recursive:
            [obj.delete() for obj in self.eAllContents()]
        seek = set(self._inverse_rels)
        # we also clean all the object references
        seek.update((self, ref) for ref in self.eClass.eAllReferences())
        for owner, feature in seek:
            fvalue = owner.eGet(feature)
            if feature.many:
                if self in fvalue:
                    fvalue.remove(self)
                    continue
                elif self is owner:
                    fvalue.clear()
                    continue
                value = next((val for val in fvalue
                              if hasattr(val, '_wrapped')
                              and val._wrapped is self),
                             None)
                if value:
                    fvalue.remove(value)
            else:
                if self is fvalue or self is owner:
                    owner.eSet(feature, None)
                    continue
                value = fvalue if (hasattr(fvalue, '_wrapped')
                                   and fvalue._wrapped is self) else None
                if value:
                    owner.eSet(feature, None)

    @property
    def eContents(self):
        children = []
        for feature in self.eClass.eAllStructuralFeatures():
            if isinstance(feature, EAttribute):
                continue
            if feature.containment:
                values = self.__getattribute__(feature.name) \
                         if feature.many \
                         else [self.__getattribute__(feature.name)]
                children.extend(filter(None, values))
        return children

    def eAllContents(self):
        objs = list(self.eContents)
        for obj in list(objs):
            objs.extend(list(obj.eAllContents()))
        return iter(objs)

    def eURIFragment(self):
        if not self.eContainer():
            return '/'
        feat = self.eContainmentFeature()
        parent = self.eContainer()
        name = feat.name
        if feat.many:
            index = parent.__getattribute__(name).index(self)
            return '{0}/@{1}.{2}' \
                   .format(parent.eURIFragment(), name, str(index))
        else:
            return '{0}/{1}'.format(parent.eURIFragment(), name)

    def eRoot(self):
        if not self.eContainer():
            return self
        if not isinstance(self.eContainer(), EObject):
            return self.eContainer()
        return self.eContainer().eRoot()


class PyEcoreValue(object):
    def __init__(self, owner, efeature=None):
        self._owner = owner
        self._efeature = efeature

    def check(self, value):
        if not EcoreUtils.isinstance(value, self._efeature.eType):
            raise BadValueError(value, self._efeature.eType)

    def _update_container(self, value, previous_value=None):
        if not isinstance(self._efeature, EReference):
            return
        if not self._efeature.containment:
            return
        if isinstance(value, EObject):
            object.__setattr__(value, '_container', self._owner)
            object.__setattr__(value, '_containment_feature', self._efeature)
            object.__setattr__(value, '_eresource', self._owner.eResource)
        elif previous_value:
            object.__setattr__(previous_value, '_container', value)
            object.__setattr__(previous_value, '_containment_feature', value)
            object.__setattr__(previous_value, '_eresource',
                               value.eResource if value else None)


class EValue(PyEcoreValue):
    def __init__(self, owner, efeature=None, value=None):
        super().__init__(owner, efeature)
        self._value = value

    def __get__(self, obj, owner=None):
        return self._value

    def __set__(self, instance, value, update_opposite=True):
        self.check(value)
        previous_value = self._value
        self._value = value
        # This case happend during meta-EReference initialization
        if not self._owner or not self._owner._isready \
                or not isinstance(self._owner, EObject):
            return
        owner = self._owner
        efeature = self._efeature
        notif = Notification(old=previous_value,
                             new=value,
                             feature=efeature,
                             kind=Kind.UNSET if value is None else Kind.SET)
        owner.notify(notif)
        if owner._isready and value != efeature.get_default_value:
            owner._isset.add(efeature)

        self._update_container(value, previous_value)
        if not isinstance(efeature, EReference) or not update_opposite:
            return

        if not efeature.eOpposite:
            couple = (owner, efeature)
            if hasattr(value, '_inverse_rels'):
                value._inverse_rels.add(couple)
                if hasattr(previous_value, '_inverse_rels'):
                    previous_value._inverse_rels.remove(couple)
            elif value is None and hasattr(previous_value, '_inverse_rels'):
                previous_value._inverse_rels.remove(couple)
            return

        if isinstance(value, EObject):
            eOpposite = efeature.eOpposite
            previous_value = value.__getattribute__(eOpposite.name)
            notif = Notification(new=owner, feature=eOpposite)
            if eOpposite.many:
                value.__getattribute__(eOpposite.name).append(owner)
                notif.kind = Kind.ADD
                value.notify(notif)
            else:
                # We disable the eOpposite update
                value.__dict__[eOpposite.name]. \
                      __set__(None, owner, update_opposite=False)
                notif.kind = Kind.SET
                value.notify(notif)
                if value._isready and \
                        eOpposite.get_default_value != owner:
                    value._isset.add(eOpposite)
        elif value is None:
            eOpposite = efeature.eOpposite
            if previous_value and eOpposite.many:
                object.__getattribute__(previous_value, eOpposite.name) \
                      .remove(owner, update_opposite=False)
            elif previous_value:
                object.__setattr__(previous_value, eOpposite.name, None)


class ECollection(PyEcoreValue):
    def create(owner, feature):
        if feature.ordered and feature.unique:
            return EOrderedSet(owner, efeature=feature)
        elif feature.ordered and not feature.unique:
            return EList(owner, efeature=feature)
        elif feature.unique:
            return ESet(owner, efeature=feature)
        else:
            return EBag(owner, efeature=feature)  # see for better implem

    def __init__(self, owner, efeature=None):
        super().__init__(owner, efeature)

    def _update_opposite(self, owner, new_value, remove=False):
        if not isinstance(self._efeature, EReference):
            return
        eOpposite = self._efeature.eOpposite
        if not eOpposite:
            couple = (new_value, self._efeature)
            if remove and couple in owner._inverse_rels:
                owner._inverse_rels.remove(couple)
            else:
                owner._inverse_rels.add(couple)
            return

        if eOpposite.many and not remove:
            owner.__getattribute__(eOpposite.name)  # force resolve
            object.__getattribute__(owner, eOpposite.name) \
                  .append(new_value, False)
        elif eOpposite.many and remove:
            object.__getattribute__(owner, eOpposite.name) \
                  .remove(new_value, False)
        else:
            new_value = None if remove else new_value
            object.__getattribute__(owner, eOpposite.name)  # Force load
            owner.__dict__[eOpposite.name] \
                 .__set__(None, new_value, update_opposite=False)

    def remove(self, value, update_opposite=True):
        if update_opposite:
            self._update_container(None, previous_value=value)
            self._update_opposite(value, self._owner, remove=True)
        super().remove(value)
        self._owner.notify(Notification(old=value,
                                        feature=self._efeature,
                                        kind=Kind.REMOVE))

    def clear(self):
        [self.remove(x) for x in self]

    def select(self, f):
        return [x for x in self if f(x)]

    def reject(self, f):
        return [x for x in self if not f(x)]


class EList(ECollection, list):
    def __init__(self, owner, efeature=None):
        super().__init__(owner, efeature)

    def append(self, value, update_opposite=True):
        self.check(value)
        if update_opposite:
            self._update_container(value)
            self._update_opposite(value, self._owner)
        super().append(value)
        self._owner.notify(Notification(new=value,
                                        feature=self._efeature,
                                        kind=Kind.ADD))
        self._owner._isset.add(self._efeature)

    def extend(self, sublist):
        all(self.check(x) for x in sublist)
        for value in sublist:
            self._update_container(value)
            self._update_opposite(value, self._owner)
        super().extend(sublist)
        self._owner.notify(Notification(new=sublist,
                                        feature=self._efeature,
                                        kind=Kind.ADD_MANY))
        self._owner._isset.add(self._efeature)

    def __setitem__(self, i, y):
        is_collection = is_iterable(y)
        if isinstance(i, slice) and is_collection:
            sliced_elements = self.__getitem__(i)
            all(self.check(x) for x in y)
            for element in y:
                self._update_container(element)
                self._update_opposite(element, self._owner)
            # We remove (not really) all element from the slice
            for element in sliced_elements:
                self._update_container(None, previous_value=element)
                self._update_opposite(element, self._owner, remove=True)
            if sliced_elements and len(sliced_elements) > 1:
                self._owner.notify(Notification(old=sliced_elements,
                                                feature=self._efeature,
                                                kind=Kind.REMOVE_MANY))
            elif sliced_elements:
                self._owner.notify(Notification(old=sliced_elements[0],
                                                feature=self._efeature,
                                                kind=Kind.REMOVE))

        else:
            self.check(y)
            self._update_container(y)
            self._update_opposite(y, self._owner)
        super().__setitem__(i, y)
        kind = Kind.ADD
        if is_collection and len(y) > 1:
            kind = Kind.ADD_MANY
        elif is_collection:
            y = y[0] if y else y
        self._owner.notify(Notification(new=y,
                                        feature=self._efeature,
                                        kind=kind))
        self._owner._isset.add(self._efeature)

    def insert(self, i, y):
        self.check(y)
        self._update_container(y)
        self._update_opposite(y, self._owner)
        super().insert(i, y)
        self._owner.notify(Notification(new=y,
                                        feature=self._efeature,
                                        kind=Kind.ADD))
        self._owner._isset.add(self._efeature)


class EBag(EList):
    def __repr__(self):
        if not self:
            return '{}()'.format(self.__class__.__name__)
        return '{}({})'.format(self.__class__.__name__, self)


class EAbstractSet(ECollection):
    def __init__(self, owner, efeature=None):
        super().__init__(owner, efeature)
        self._orderedset_update = False

    def append(self, value, update_opposite=True):
        self.add(value, update_opposite)

    def add(self, value, update_opposite=True):
        self.check(value)
        if update_opposite:
            self._update_container(value)
            self._update_opposite(value, self._owner)
        super().add(value)
        if not self._orderedset_update:
            self._owner.notify(Notification(new=value,
                                            feature=self._efeature,
                                            kind=Kind.ADD))
        self._owner._isset.add(self._efeature)

    def extend(self, sublist):
        self.update(*sublist)

    def update(self, *others):
        all(self.check(x) for x in others)
        for value in others:
            self._update_container(value)
            self._update_opposite(value, self._owner)
        super().update(others)
        self._owner.notify(Notification(new=others,
                                        feature=self._efeature,
                                        kind=Kind.ADD_MANY))
        self._owner._isset.add(self._efeature)


class EOrderedSet(EAbstractSet, OrderedSet):
    def __init__(self, owner, efeature=None):
        super().__init__(owner, efeature)
        OrderedSet.__init__(self)

    def update(self, *others):
        self._orderedset_update = True
        OrderedSet.update(self, others)
        self._owner.notify(Notification(new=others,
                                        feature=self._efeature,
                                        kind=Kind.ADD_MANY))
        self._owner._isset.add(self._efeature)
        self._orderedset_update = False


class ESet(EOrderedSet):
    pass


class EModelElement(EObject):
    def __init__(self):
        super().__init__()

    def eURIFragment(self):
        if not self.eContainer():
            return '#/'
        parent = self.eContainer()
        if hasattr(self, 'name') and self.name:
            return '{0}/{1}'.format(parent.eURIFragment(), self.name)
        else:
            return super().eURIFragment()


class EAnnotation(EModelElement):
    def __init__(self, source=None):
        super().__init__()
        self.source = source
        self.details = {}


class ENamedElement(EModelElement):
    def __init__(self, name=None):
        super().__init__()
        self.name = name


class EPackage(ENamedElement):
    def __init__(self, name=None, nsURI=None, nsPrefix=None):
        super().__init__(name)
        self.nsURI = nsURI
        self.nsPrefix = nsPrefix

    def getEClassifier(self, name):
        return next((c for c in self.eClassifiers if c.name == name), None)


class ETypedElement(ENamedElement):
    def __init__(self, name=None, eType=None, ordered=True, unique=True,
                 lower=0, upper=1, required=False):
        super().__init__(name)
        self.eType = eType
        self.lowerBound = int(lower)
        self.upperBound = int(upper)
        self.ordered = ordered
        self.unique = unique
        self.required = required

    @property
    def many(self):
        return int(self.upperBound) > 1 or int(self.upperBound) < 0


class EOperation(ETypedElement):
    def __init__(self, name=None, eType=None, params=None, exceptions=None):
        super().__init__(name, eType)
        if params:
            for param in params:
                self.eParameters.append(param)
        if exceptions:
            for exception in exceptions:
                self.eExceptions.append(exception)

    def normalized_name(self):
        name = self.name
        if keyword.iskeyword(name):
            name = '_' + name
        return name

    def to_code(self):
        parameters = [x.to_code() for x in self.eParameters]
        return """def {0}(self, {1}):
        raise NotImplementedError('Method {0}({1}) is not yet implemented')
        """.format(self.normalized_name(), ', '.join(parameters))


class EParameter(ETypedElement):
    def __init__(self, name=None, eType=None, required=False):
        super().__init__(name, eType, required=required)

    def to_code(self):
        if self.required:
            return "{0}".format(self.name)
        if hasattr(self.eType, 'default_value'):
            default_value = self.eType.default_value
        else:
            default_value = None
        return "{0}={1}".format(self.name, default_value)


class ETypeParameter(ENamedElement):
    def __init__(self, name=None):
        super().__init__(name)


class EGenericType(EObject):
    def __init__(self):
        super().__init__()


class EClassifier(ENamedElement):
    def __init__(self, name=None):
        super().__init__(name)


class EDataType(EClassifier):
    javaTransMap = {'java.lang.String': str,
                    'boolean': bool,
                    'java.lang.Boolean': bool,
                    'byte': int,
                    'int': int,
                    'java.lang.Integer': int,
                    'java.lang.Class': type,
                    'java.util.Map': {},
                    'java.util.Map$Entry': {},
                    'double': int,
                    'java.lang.Double': int,
                    'char': str,
                    'java.lang.Character': str}  # Must be completed

    def __init__(self, name=None, eType=None, default_value=None,
                 from_string=None, to_string=None):
        super().__init__(name)
        self.eType = eType
        self._instanceClassName = None
        self.default_value = default_value
        if from_string:
            self.from_string = from_string
        if to_string:
            self.to_string = to_string

    def from_string(self, value):
        return value

    def to_string(self, value):
        return str(value)

    @property
    def instanceClassName(self):
        return self._instanceClassName

    @instanceClassName.setter
    def instanceClassName(self, name):
        self._instanceClassName = name
        try:
            self.eType = self.javaTransMap[name]
        except KeyError:
            pass

    def __repr__(self):
        etype = self.eType.__name__ if self.eType else None
        return '{0}({1})'.format(self.name, etype)


class EEnum(EDataType):
    def __init__(self, name=None, default_value=None, literals=None):
        super().__init__(name, eType=self)
        if literals:
            for i, lit_name in enumerate(literals):
                lit_name = '_' + lit_name if lit_name[:1].isnumeric() \
                                          else lit_name
                literal = EEnumLiteral(i, lit_name)
                self.eLiterals.append(literal)
                self.__setattr__(lit_name, literal)
        if default_value:
            self.default_value = self.__getattribute__(default_value)
        elif not default_value and literals:
            self.default_value = self.eLiterals[0]

    def __contains__(self, key):
        if isinstance(key, EEnumLiteral):
            return key in self.eLiterals
        return any(lit for lit in self.eLiterals if lit.name == key)

    def getEEnumLiteral(self, name=None, value=0):
        try:
            if name:
                return next(lit for lit in self.eLiterals if lit.name == name)
            return next(lit for lit in self.eLiterals if lit.value == value)
        except StopIteration:
            return None

    def __repr__(self):
        name = self.name or ''
        return name + str(self.eLiterals)


class EEnumLiteral(ENamedElement):
    def __init__(self, value=0, name=None):
        super().__init__(name)
        self.value = value

    def __repr__(self):
        return '{0}={1}'.format(self.name, self.value)


class EStructuralFeature(ETypedElement):
    def __init__(self, name=None, eType=None, ordered=True, unique=True,
                 lower=0, upper=1, required=False, changeable=True,
                 volatile=False, transient=False, unsettable=False,
                 derived=False):
        super().__init__(name, eType, ordered, unique, lower, upper, required)
        self.changeable = changeable
        self.volatile = volatile
        self.transient = transient
        self.unsettable = unsettable
        self.derived = derived
        self._name = name

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        name = self._name
        if name not in instance.__dict__.keys():
            if self.many:
                new_value = ECollection.create(instance, self)
            else:
                new_value = EValue(instance, self)
            instance.__dict__[name] = new_value
        value = instance.__dict__[name]
        if isinstance(value, EValue):
            return value.__get__(instance, owner)
        else:
            return value

    def __set__(self, instance, value):
        name = self._name
        if isinstance(value, ECollection):
            instance.__dict__[name] = value
            return
        if name not in instance.__dict__.keys():
            evalue = EValue(instance, self)
            instance.__dict__[name] = evalue
        previous_value = instance.__dict__[name]
        if isinstance(previous_value, ECollection):
            raise BadValueError(got=value, expected=previous_value.__class__)
        instance.__dict__[name].__set__(instance, value)

    def __repr__(self):
        eType = self.eType if hasattr(self, 'eType') else None
        name = self.name if hasattr(self, 'name') else None
        return '<EStructuralFeature {0}: {1}>'.format(name, eType)


class EAttribute(EStructuralFeature):
    def __init__(self, name=None, eType=None, default_value=None,
                 lower=0, upper=1, changeable=True, derived=False,
                 unique=True, ordered=True):
        super().__init__(name, eType, lower=lower, upper=upper,
                         derived=derived, changeable=changeable,
                         unique=unique, ordered=ordered)
        self.default_value = default_value
        if not self.default_value and isinstance(eType, EDataType):
            self.default_value = eType.default_value

    def get_default_value(self):
        if self.default_value is not None:
            return self.default_value
        return self.eType.default_value


class EReference(EStructuralFeature):
    def __init__(self, name=None, eType=None, lower=0, upper=1,
                 containment=False, eOpposite=None, ordered=True, unique=True,
                 derived=False):
        super().__init__(name, eType, ordered, unique, lower=lower,
                         upper=upper, derived=derived)
        self.containment = containment
        self.eOpposite = eOpposite
        if not isinstance(eType, EClass) and hasattr(eType, 'eClass'):
            self.eType = eType.eClass

    def get_default_value(self):
        return None

    @property
    def eOpposite(self):
        return self._eopposite

    @eOpposite.setter
    def eOpposite(self, value):
        self._eopposite = value
        if value:
            value._eopposite = self


class EClass(EClassifier):
    def __init__(self, name=None, superclass=None, abstract=False,
                 metainstance=None):
        super().__init__(name)
        self.abstract = abstract
        self._staticEClass = False
        if isinstance(superclass, tuple):
            [self.eSuperTypes.append(x) for x in superclass]
        elif isinstance(superclass, EClass):
            self.eSuperTypes.append(superclass)
        if metainstance:
            self._metainstance = metainstance
        else:
            self._metainstance = type(self.name,
                                      self.__compute_supertypes(),
                                      {
                                          'eClass': self,
                                          '_staticEClass': self._staticEClass,
                                      })
        self.supertypes_updater = EObserver()
        self.supertypes_updater.notifyChanged = self.__update
        self._eternal_listener.append(self.supertypes_updater)

    def __call__(self, *args, **kwargs):
        if self.abstract:
            raise TypeError("Can't instantiate abstract EClass {0}"
                            .format(self.name))
        obj = self._metainstance()
        obj._isready = True
        return obj

    def __update(self, notif):
        # We do not update in case of static metamodel (could be changed)
        if hasattr(self.python_class, '_staticEClass') \
                and self.python_class._staticEClass:
            return
        if notif.feature is EClass.eSuperTypes:
            new_supers = self.__compute_supertypes()
            self._metainstance.__bases__ = new_supers
        elif notif.feature is EClass.eOperations:
            if notif.kind is Kind.ADD:
                self.__create_fun(notif.new)
            elif notif.kind is Kind.REMOVE:
                delattr(self.python_class, notif.new.name)
        elif notif.feature is EClass.eStructuralFeatures:
            if notif.kind is Kind.ADD:
                setattr(self.python_class, notif.new.name, notif.new)
            elif notif.kind is Kind.REMOVE:
                delattr(self.python_class, notif.new.name)

    def __create_fun(self, eoperation):
        name = eoperation.normalized_name()
        namespace = {}
        code = compile(eoperation.to_code(), "<str>", "exec")
        exec(code, namespace)
        setattr(self.python_class, name, namespace[name])

    def __compute_supertypes(self):
        if not self.eSuperTypes:
            return (EObject,)
        else:
            eSuperTypes = list(self.eSuperTypes)
            return tuple(x._metainstance for x in eSuperTypes)

    @property
    def python_class(self):
        return self._metainstance

    def __repr__(self):
        return '<EClass name="{0}">'.format(self.name)

    @property
    def eAttributes(self):
        return [x for x in self.eStructuralFeatures
                if isinstance(x, EAttribute)]

    @property
    def eReferences(self):
        return [x for x in self.eStructuralFeatures
                if isinstance(x, EReference)]

    def findEStructuralFeature(self, name):
        struct = next(
            (f for f in self.eStructuralFeatures if f.name == name),
            None)
        if struct:
            return struct
        if not self.eSuperTypes:
            return None
        for stype in self.eSuperTypes:
            struct = stype.findEStructuralFeature(name)
            if struct:
                break
        return struct

    def eAllSuperTypes(self):
        # if isinstance(self, type):
        #     return (x.eClass for x in self.mro() if x is not object and
        #             x is not self)
        if not self.eSuperTypes:
            return iter(set())
        result = set()
        for stype in self.eSuperTypes:
            result.add(stype)
            result |= frozenset(stype.eAllSuperTypes())
        return result

    def eAllStructuralFeatures(self):
        features = set(self.eStructuralFeatures)
        for feature in self.eAllSuperTypes():
            features.update(feature.eStructuralFeatures)
        return features

    def eAllReferences(self):
        return set((x for x in self.eAllStructuralFeatures()
                    if isinstance(x, EReference)))

    def eAllOperations(self):
        operations = set(self.eOperations)
        for superclass in self.eAllSuperTypes():
            operations.update(superclass.eOperations)
        return operations

    def findEOperation(self, name):
        operation = next((f for f in self.eOperations if f.name == name), None)
        if operation:
            return operation
        if not self.eSuperTypes:
            return None
        for stype in self.eSuperTypes:
            operation = stype.findEOperation(name)
            if operation:
                break
        return operation


# Meta methods for static EClass
class MetaEClass(type):
    def __init__(cls, name, bases, nmspc):
        super().__init__(name, bases, nmspc)
        Core.register_classifier(cls, promote=True)
        cls._staticEClass = True

    def __call__(cls, *args, **kwargs):
        if cls.eClass.abstract:
            raise TypeError("Can't instantiate abstract EClass {0}"
                            .format(cls.eClass.name))
        obj = type.__call__(cls, *args, **kwargs)
        # init instances by reflection
        if not hasattr(obj, '_isready'):
            EObject.__subinit__(obj)
        # required for 'at runtime' added features
        for efeat in reversed(list(obj.eClass.eAllStructuralFeatures())):
            if efeat.name in obj.__dict__:
                continue
            if isinstance(efeat, EAttribute):
                obj.__setattr__(efeat.name, efeat.default_value)
            elif efeat.many:
                obj.__setattr__(efeat.name, ECollection.create(obj, efeat))
            else:
                obj.__setattr__(efeat.name, None)
        obj._isready = True
        return obj


class EProxy(EObject):
    def __init__(self, path=None, resource=None, wrapped=None):
        object.__setattr__(self, '_wrapped', wrapped)
        object.__setattr__(self, '_proxy_path', path)
        object.__setattr__(self, '_proxy_resource', resource)
        object.__setattr__(self, '_resolved', wrapped is not None)
        object.__setattr__(self, '_inverse_rels', set())

    def force_resolve(self):
        if self._resolved:
            return
        resource = self._proxy_resource
        decoders = resource._get_href_decoder(self._proxy_path)
        self._wrapped = decoders.resolve(self._proxy_path, resource)
        self._wrapped._inverse_rels.update(self._inverse_rels)
        self._inverse_rels = self._wrapped._inverse_rels
        self._resolved = True

    def delete(self, recursive=True):
        if recursive and self._resolved:
            [obj.delete() for obj in self.eAllContents()]

        seek = set(self._inverse_rels)
        if self._resolved:
            seek.update((self, ref) for ref in self.eClass.eAllReferences())
        for owner, feature in seek:
            fvalue = owner.eGet(feature)
            if feature.many:
                if self in fvalue:
                    fvalue.remove(self)
                    continue
                if owner is self:
                    fvalue.clear()
                    continue
                value = next((val for val in fvalue
                              if self._wrapped is val),
                             None)
                if value:
                    fvalue.remove(value)
            else:
                if self is fvalue or owner is self:
                    owner.eSet(feature, None)
                    continue
                value = fvalue if self._wrapped is fvalue else None
                if value:
                    owner.eSet(feature, None)

    def __getattribute__(self, name):
        if name in ['_wrapped', '_proxy_path', '_proxy_resource', '_resolved',
                    'force_resolve', 'delete']:
            return object.__getattribute__(self, name)
        resolved = object.__getattribute__(self, '_resolved')
        if not resolved:
            if name in ['__class__', '_inverse_rels']:
                return object.__getattribute__(self, name)
            resource = self._proxy_resource
            decoders = resource._get_href_decoder(self._proxy_path)
            self._wrapped = decoders.resolve(self._proxy_path, resource)
            self._wrapped._inverse_rels.update(self._inverse_rels)
            self._inverse_rels = self._wrapped._inverse_rels
            self._resolved = True
        wrapped = self._wrapped
        return wrapped.__getattribute__(name)

    def __setattr__(self, name, value):
        if name in ['_wrapped', '_proxy_path', '_resolved', '_proxy_resource']:
            object.__setattr__(self, name, value)
            return
        resolved = self._resolved
        if not resolved:
            resource = self._proxy_resource
            decoders = resource._get_href_decoder(self._proxy_path)
            self._wrapped = decoders.resolve(self._proxy_path, resource)
            self._resolved = True
        wrapped = self._wrapped
        wrapped.__setattr__(name, value)


def abstract(cls):
    cls.eClass.abstract = True
    return cls


# meta-meta level
EString = EDataType('EString', str)
EBoolean = EDataType('EBoolean', bool, False,
                     to_string=lambda x: str(x).lower(),
                     from_string=lambda x: x in ['True', 'true'])
EInteger = EDataType('EInteger', int, 0, from_string=lambda x: int(x))
EInt = EDataType('EInt', int, 0, from_string=lambda x: int(x))
ELong = EDataType('ELong', int, 0, from_string=lambda x: int(x))
EIntegerObject = EDataType('EIntegerObject', int, from_string=lambda x: int(x))
EBigInteger = EDataType('EBigInteger', int, from_string=lambda x: int(x))
EDouble = EDataType('EDouble', float, 0.0, from_string=lambda x: float(x))
EDoubleObject = EDataType('EDoubleObject', float, 0.0,
                          from_string=lambda x: float(x))
EFloat = EDataType('EFloat', float, 0.0, from_string=lambda x: float(x))
EFloatObject = EDataType('EFloatObject', float, 0.0,
                         from_string=lambda x: float(x))
EStringToStringMapEntry = EDataType('EStringToStringMapEntry', dict, {})
EDiagnosticChain = EDataType('EDiagnosticChain', str)
ENativeType = EDataType('ENativeType', object)
EJavaObject = EDataType('EJavaObject', object)

ENamedElement.name = EAttribute('name', EString)

EModelElement.eAnnotations = EReference('eAnnotations', EAnnotation,
                                        upper=-1, containment=True)
EAnnotation.eModelElement = EReference('eModelElement', EModelElement,
                                       eOpposite=EModelElement.eAnnotations)
EAnnotation.source = EAttribute('source', EString)
EAnnotation.details = EAttribute('details', EStringToStringMapEntry)
EAnnotation.references = EReference('references', EObject, upper=-1)
EAnnotation.contents = EReference('contents', EObject, upper=-1)

ETypedElement.ordered = EAttribute('ordered', EBoolean, default_value=True)
ETypedElement.unique = EAttribute('unique', EBoolean, default_value=True)
ETypedElement.lower = EAttribute('lower', EInteger, derived=True)
ETypedElement.lowerBound = EAttribute('lowerBound', EInteger)
ETypedElement.upper = EAttribute('upper', EInteger,
                                 default_value=1, derived=True)
ETypedElement.upperBound = EAttribute('upperBound', EInteger, default_value=1)
ETypedElement.required = EAttribute('required', EBoolean)
ETypedElement.eType = EReference('eType', EClassifier)
# ETypedElement.default_value = EAttribute('default_value', ENativeType)

EStructuralFeature.changeable = EAttribute('changeable', EBoolean,
                                           default_value=True)
EStructuralFeature.volatile = EAttribute('volatile', EBoolean)
EStructuralFeature.transient = EAttribute('transient', EBoolean)
EStructuralFeature.unsettable = EAttribute('unsettable', EBoolean)
EStructuralFeature.derived = EAttribute('derived', EBoolean)
EStructuralFeature.defaultValueLiteral = EAttribute('defaultValueLiteral',
                                                    EString)


EPackage.nsURI = EAttribute('nsURI', EString)
EPackage.nsPrefix = EAttribute('nsPrefix', EString)
EPackage.eClassifiers = EReference('eClassifiers', EClassifier,
                                   upper=-1, containment=True)
EPackage.eSubpackages = EReference('eSubpackages', EPackage,
                                   upper=-1, containment=True)
EPackage.eSuperPackage = EReference('eSuperPackage', EPackage,
                                    lower=1, eOpposite=EPackage.eSubpackages)

EClassifier.ePackage = EReference('ePackage', EPackage,
                                  eOpposite=EPackage.eClassifiers)
EClassifier.eTypeParameters = EReference('eTypeParameters', ETypeParameter,
                                         upper=-1, containment=True)

EDataType._instanceClassName = EAttribute('instanceClassName', EString)
EDataType.serializable = EAttribute('serializable', EBoolean)

EClass.abstract = EAttribute('abstract', EBoolean)
EClass.eStructuralFeatures = EReference('eStructuralFeatures',
                                        EStructuralFeature,
                                        upper=-1, containment=True)
EClass._eAttributes = EReference('eAttributes', EAttribute,
                                 upper=-1, derived=True)
EClass._eReferences = EReference('eReferences', EReference,
                                 upper=-1, derived=True)
EClass.eSuperTypes = EReference('eSuperTypes', EClass, upper=-1)
EClass.eOperations = EReference('eOperations', EOperation,
                                upper=-1, containment=True)
EClass.instanceClassName = EAttribute('instanceClassName', EString)
EClass.interface = EAttribute('interface', EBoolean)

EStructuralFeature.eContainingClass = \
                   EReference('eContainingClass', EClass,
                              eOpposite=EClass.eStructuralFeatures)

EReference.containment = EAttribute('containment', EBoolean)
EReference._eOpposite = EReference('eOpposite', EReference)
EReference.resolveProxies = EAttribute('resolveProxies', EBoolean)

EEnum.eLiterals = EReference('eLiterals', EEnumLiteral, upper=-1,
                             containment=True)

EEnumLiteral.eEnum = EReference('eEnum', EEnum, eOpposite=EEnum.eLiterals)
EEnumLiteral.name = EAttribute('name', EString)
EEnumLiteral.value = EAttribute('value', EInteger)
EEnumLiteral.literal = EAttribute('literal', EString)

EOperation.eContainingClass = EReference('eContainingClass', EClass,
                                         eOpposite=EClass.eOperations)
EOperation.eParameters = EReference('eParameters', EParameter, upper=-1)
EOperation.eExceptions = EReference('eExceptions', EClassifier, upper=-1)
EOperation.eTypeParameters = EReference('eTypeParameters', ETypeParameter,
                                        upper=-1, containment=True)

EParameter.eOperation = EReference('eOperation', EOperation,
                                   eOpposite=EOperation.eParameters)

ETypeParameter.eBounds = EReference('eBounds', EGenericType,
                                    upper=-1, containment=True)
ETypeParameter.eGenericType = EReference('eGenericType', EGenericType,
                                         upper=-1)

eClass = EPackage(name=name, nsURI=nsURI, nsPrefix=nsPrefix)
Core.register_classifier(EModelElement, promote=True)
Core.register_classifier(ENamedElement, promote=True)
Core.register_classifier(EAnnotation, promote=True)
Core.register_classifier(EPackage, promote=True)
Core.register_classifier(EGenericType, promote=True)
Core.register_classifier(ETypeParameter, promote=True)
Core.register_classifier(ETypedElement, promote=True)
Core.register_classifier(EClassifier, promote=True)
Core.register_classifier(EDataType, promote=True)
Core.register_classifier(EEnum, promote=True)
Core.register_classifier(EEnumLiteral, promote=True)
Core.register_classifier(EParameter, promote=True)
Core.register_classifier(EOperation, promote=True)
Core.register_classifier(EClass, promote=True)
Core.register_classifier(EStructuralFeature, promote=True)
Core.register_classifier(EAttribute, promote=True)
Core.register_classifier(EReference, promote=True)
Core.register_classifier(EString)
Core.register_classifier(EBoolean)
Core.register_classifier(EInteger)
Core.register_classifier(EInt)
Core.register_classifier(EBigInteger)
Core.register_classifier(EIntegerObject)
Core.register_classifier(EFloat)
Core.register_classifier(EFloatObject)
Core.register_classifier(EDouble)
Core.register_classifier(EDoubleObject)
Core.register_classifier(EStringToStringMapEntry)
Core.register_classifier(EDiagnosticChain)
Core.register_classifier(ENativeType)
Core.register_classifier(EJavaObject)


__all__ = ['EObject', 'EModelElement', 'ENamedElement', 'EAnnotation',
           'EPackage', 'EGenericType', 'ETypeParameter', 'ETypedElement',
           'EClassifier', 'EDataType', 'EEnum', 'EEnumLiteral', 'EParameter',
           'EOperation', 'EClass', 'EStructuralFeature', 'EAttribute',
           'EReference', 'EString', 'EBoolean', 'EInteger',
           'EStringToStringMapEntry', 'EDiagnosticChain', 'ENativeType',
           'EJavaObject', 'abstract', 'MetaEClass', 'EList', 'ECollection',
           'EOrderedSet', 'ESet', 'EcoreUtils', 'BadValueError', 'EDouble',
           'EDoubleObject', 'EBigInteger', 'EInt', 'EIntegerObject', 'EFloat',
           'EFloatObject', 'ELong', 'EProxy']
