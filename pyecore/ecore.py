"""This module is the heart of PyEcore. It defines all the basic concepts that
are common to EMF-Java and PyEcore (EObject/EClass...).
It defines the basic classes and behavior for PyEcore implementation:

* EObject
* EPackage
* EClass
* EAttribute
* EReference
* EDataType
* EcoreUtils

These concepts are enough if dynamic metamodel instance are handled (code
generation is not required).

In addition, ``@EMetaclass`` annotation and ``MetaEClass`` metaclass are
used for static metamodels definition.
"""
from functools import partial
import sys
import keyword
import inspect
from decimal import Decimal
from datetime import datetime
from .ordered_set_patch import ordered_set
from ordered_set import OrderedSet
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
    """
    Gets the default root URI fragment.

    :return: the root URI fragment
    :rtype: str
    """
    return '/'


def eURIFragment():
    """
    Gets the URI fragment for the Ecore module.

    :return: the root URI fragment for Ecore
    :rtype: str
    """
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
    @staticmethod
    def isinstance(obj, _type):
        if obj is None:
            return True
        elif isinstance(obj, EProxy) and not obj.resolved:
            return True
        elif isinstance(obj, _type):
            return True
        return _type.__isinstance__(obj)

    @staticmethod
    def getRoot(obj):
        if not obj:
            return None
        previous = obj
        while previous.eContainer() is not None:
            previous = previous.eContainer()
        return previous


class Core(object):
    @staticmethod
    def _promote(cls, abstract=False):
        cls.eClass = EClass(cls.__name__, metainstance=cls)
        cls.eClass.abstract = abstract
        cls._staticEClass = True
        # init super types
        eSuperTypes_add = cls.eClass.eSuperTypes.append
        for _cls in cls.__bases__:
            if _cls is EObject:
                continue
            try:
                eSuperTypes_add(_cls.eClass)
            except Exception:
                pass
        # init eclass by reflection
        eStructuralFeatures_add = cls.eClass.eStructuralFeatures.append
        for k, feature in cls.__dict__.items():
            if isinstance(feature, EStructuralFeature):
                if not feature.name:
                    feature.name = k
                eStructuralFeatures_add(feature)
            elif inspect.isfunction(feature):
                if k.startswith('__'):
                    continue
                argspect = inspect.getfullargspec(feature)
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

    @staticmethod
    def register_classifier(cls, abstract=False, promote=False):
        if promote:
            Core._promote(cls, abstract)
        epackage = sys.modules[cls.__module__]
        if not hasattr(epackage, 'eClassifiers'):
            eclassifs = {}
            epackage.eClassifiers = eclassifs
            epackage.getEClassifier = partial(getEClassifier,
                                              searchspace=eclassifs)
        if not hasattr(epackage, 'eClass'):
            pack_name = (epackage.__name__ if epackage.__name__ != '__main__'
                         else 'default_package')
            epackage.eClass = EPackage(name=pack_name,
                                       nsPrefix=pack_name,
                                       nsURI='http://{}/'.format(pack_name))
        if not hasattr(epackage, 'eURIFragment'):
            epackage.eURIFragment = eURIFragment
        cname = cls.name if isinstance(cls, EClassifier) else cls.__name__
        epackage.eClassifiers[cname] = cls
        if isinstance(cls, EDataType):
            epackage.eClass.eClassifiers.append(cls)
            cls._container = epackage
        else:
            epackage.eClass.eClassifiers.append(cls.eClass)
            cls.eClass._container = epackage


class EObject(ENotifer):
    _staticEClass = True

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        instance._xmiid = None
        instance._isset = set()
        instance._container = None
        instance._containment_feature = None
        instance._eresource = None
        instance.listeners = []
        instance._eternal_listener = []
        instance._inverse_rels = set()
        instance._staticEClass = False
        return instance

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

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
        if self.eContainer():
            try:
                return self.eContainer().eResource
            except AttributeError:
                pass
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
                              if getattr(val, '_wrapped', None) is self),
                             None)
                if value:
                    fvalue.remove(value)
            else:
                if self is fvalue or self is owner:
                    owner.eSet(feature, None)
                    continue
                value = (fvalue if getattr(fvalue, '_wrapped', None) is self
                         else None)
                if value:
                    owner.eSet(feature, None)

    @property
    def eContents(self):
        children = []
        for feature in self.eClass.eAllReferences():
            if not feature.containment:
                continue
            if feature.many:
                values = self.__getattribute__(feature.name)
            else:
                values = [self.__getattribute__(feature.name)]
            children.extend((x for x in values if x))
        return children

    def eAllContents(self):
        contents = self.eContents
        for x in contents:
            yield x
        for x in contents:
            yield from x.eAllContents()

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

    def __dir__(self):
        eclass = self.eClass
        relevant = [x.name for x in eclass.eAllStructuralFeatures()]
        relevant.extend([x.name for x in eclass.eAllOperations()
                        if not x.name.startswith('_')])
        return relevant


class PyEcoreValue(object):
    def __init__(self, owner, efeature):
        super().__init__()
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
        elif previous_value:
            object.__setattr__(previous_value, '_container', value)
            object.__setattr__(previous_value, '_containment_feature', value)


class EValue(PyEcoreValue):
    def __init__(self, owner, efeature):
        super().__init__(owner, efeature)
        self._value = efeature.get_default_value()

    def _get(self):
        return self._value

    def _set(self, value, update_opposite=True):
        self.check(value)
        previous_value = self._value
        self._value = value
        owner = self._owner
        efeature = self._efeature
        notif = Notification(old=previous_value,
                             new=value,
                             feature=efeature,
                             kind=Kind.UNSET if value is None else Kind.SET)
        owner.notify(notif)
        owner._isset.add(efeature)

        if not isinstance(efeature, EReference):
            return
        self._update_container(value, previous_value)
        if not update_opposite:
            return

        # if there is no opposite, we set inverse relation and return
        if not efeature.eOpposite:
            couple = (owner, efeature)
            if hasattr(value, '_inverse_rels'):
                if hasattr(previous_value, '_inverse_rels'):
                    previous_value._inverse_rels.remove(couple)
                value._inverse_rels.add(couple)
            elif value is None and hasattr(previous_value, '_inverse_rels'):
                previous_value._inverse_rels.remove(couple)
            return

        eOpposite = efeature.eOpposite
        # if we are in an 'unset' context
        if value is None:
            if previous_value is None:
                return
            if eOpposite.many:
                object.__getattribute__(previous_value, eOpposite.name) \
                      .remove(owner, update_opposite=False)
            else:
                object.__setattr__(previous_value, eOpposite.name, None)
        else:
            previous_value = value.__getattribute__(eOpposite.name)
            if eOpposite.many:
                value.__getattribute__(eOpposite.name) \
                     .append(owner, update_opposite=False)
            else:
                # We disable the eOpposite update
                value.__dict__[eOpposite.name]. \
                      _set(owner, update_opposite=False)


class ECollection(PyEcoreValue):
    @staticmethod
    def create(owner, feature):
        if feature.ordered and feature.unique:
            return EOrderedSet(owner, feature)
        elif feature.ordered and not feature.unique:
            return EList(owner, feature)
        elif feature.unique:
            return ESet(owner, feature)
        else:
            return EBag(owner, feature)  # see for better implem

    def __init__(self, owner, efeature):
        super().__init__(owner, efeature)

    def _get(self):
        return self

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
            owner.__getattribute__(eOpposite.name).append(new_value, False)
        elif eOpposite.many and remove:
            owner.__getattribute__(eOpposite.name).remove(new_value, False)
        else:
            new_value = None if remove else new_value
            owner.__getattribute__(eOpposite.name)  # Force load
            owner.__dict__[eOpposite.name] \
                 ._set(new_value, update_opposite=False)

    def remove(self, value, update_opposite=True):
        self._update_container(None, previous_value=value)
        if update_opposite:
            self._update_opposite(value, self._owner, remove=True)
        super().remove(value)
        self._owner.notify(Notification(old=value,
                                        feature=self._efeature,
                                        kind=Kind.REMOVE))

    def insert(self, i, y):
        self.check(y)
        self._update_container(y)
        self._update_opposite(y, self._owner)
        super().insert(i, y)
        self._owner.notify(Notification(new=y,
                                        feature=self._efeature,
                                        kind=Kind.ADD))
        self._owner._isset.add(self._efeature)

    def pop(self, index=None):
        if index is None:
            value = super().pop()
        else:
            value = super().pop(index)
        self._update_container(None, previous_value=value)
        self._update_opposite(value, self._owner, remove=True)
        self._owner.notify(Notification(old=value,
                                        feature=self._efeature,
                                        kind=Kind.REMOVE))
        return value

    def clear(self):
        [self.remove(x) for x in set(self)]

    def select(self, f):
        return [x for x in self if f(x)]

    def reject(self, f):
        return [x for x in self if not f(x)]

    def __iadd__(self, items):
        if ordered_set.is_iterable(items):
            self.extend(items)
        else:
            self.append(items)
        return self


class EList(ECollection, list):
    def __init__(self, owner, efeature=None):
        super().__init__(owner, efeature)

    def append(self, value, update_opposite=True):
        self.check(value)
        self._update_container(value)
        if update_opposite:
            self._update_opposite(value, self._owner)
        super().append(value)
        self._owner.notify(Notification(new=value,
                                        feature=self._efeature,
                                        kind=Kind.ADD))
        self._owner._isset.add(self._efeature)

    def extend(self, sublist):
        for x in sublist:
            self.check(x)
        for value in sublist:
            self._update_container(value)
            self._update_opposite(value, self._owner)
        super().extend(sublist)
        self._owner.notify(Notification(new=sublist,
                                        feature=self._efeature,
                                        kind=Kind.ADD_MANY))
        self._owner._isset.add(self._efeature)

    def __setitem__(self, i, y):
        is_collection = ordered_set.is_iterable(y)
        if isinstance(i, slice) and is_collection:
            sliced_elements = self.__getitem__(i)
            for element in y:
                self.check(element)
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


class EBag(EList):
    pass


class EAbstractSet(ECollection):
    def __init__(self, owner, efeature=None):
        super().__init__(owner, efeature)
        self._orderedset_update = False

    def append(self, value, update_opposite=True):
        self.add(value, update_opposite)

    def add(self, value, update_opposite=True):
        self.check(value)
        self._update_container(value)
        if update_opposite:
            self._update_opposite(value, self._owner)
        super().add(value)
        if not self._orderedset_update:
            self._owner.notify(Notification(new=value,
                                            feature=self._efeature,
                                            kind=Kind.ADD))
        self._owner._isset.add(self._efeature)

    def extend(self, sublist):
        self.update(sublist)

    def update(self, others):
        for x in others:
            self.check(x)
        for value in others:
            self._update_container(value)
            self._update_opposite(value, self._owner)
        super().update(others)
        self._owner.notify(Notification(new=others,
                                        feature=self._efeature,
                                        kind=Kind.ADD_MANY))
        self._owner._isset.add(self._efeature)


class EOrderedSet(EAbstractSet, ordered_set.OrderedSet):
    def __init__(self, owner, efeature=None):
        super().__init__(owner, efeature)
        ordered_set.OrderedSet.__init__(self)

    def update(self, others):
        self._orderedset_update = True
        super().update(others)
        self._orderedset_update = False


class ESet(EOrderedSet):
    pass


class EModelElement(EObject):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def eURIFragment(self):
        if not self.eContainer():
            return '#/'
        parent = self.eContainer()
        if getattr(self, 'name', None):
            return '{0}/{1}'.format(parent.eURIFragment(), self.name)
        else:
            return super().eURIFragment()

    def getEAnnotation(self, source):
        """Return the annotation with a matching source attribute."""
        for annotation in self.eAnnotations:
            if annotation.source == source:
                return annotation
        return None


class EAnnotation(EModelElement):
    def __init__(self, source=None, **kwargs):
        super().__init__(**kwargs)
        self.source = source
        self.details = {}


class ENamedElement(EModelElement):
    def __init__(self, name=None, **kwargs):
        super().__init__(**kwargs)
        self.name = name


class EPackage(ENamedElement):
    def __init__(self, name=None, nsURI=None, nsPrefix=None, **kwargs):
        super().__init__(name, **kwargs)
        self.nsURI = nsURI
        self.nsPrefix = nsPrefix

    def getEClassifier(self, name):
        return next((c for c in self.eClassifiers if c.name == name), None)

    @staticmethod
    def __isinstance__(self, instance=None):
        return (instance is None and
                (isinstance(self, EPackage) or
                 inspect.ismodule(self) and hasattr(self, 'nsURI')))


class ETypedElement(ENamedElement):
    def __init__(self, name=None, eType=None, ordered=True, unique=True,
                 lower=0, upper=1, required=False, **kwargs):
        super().__init__(name, **kwargs)
        self.eType = eType
        self.lowerBound = int(lower)
        self.upperBound = int(upper)
        self.ordered = ordered
        self.unique = unique
        self.required = required

    @property
    def many(self):
        return self.upperBound > 1 or self.upperBound < 0


class EOperation(ETypedElement):
    def __init__(self, name=None, eType=None, params=None, exceptions=None,
                 **kwargs):
        super().__init__(name, eType, **kwargs)
        if params:
                self.eParameters.extend(params)
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
        if len(parameters) == 0 or parameters[0] != 'self':
            parameters.insert(0, 'self')
        return """def {0}({1}):
        raise NotImplementedError('Method {0}({1}) is not yet implemented')
        """.format(self.normalized_name(), ', '.join(parameters))


class EParameter(ETypedElement):
    def __init__(self, name=None, eType=None, **kwargs):
        super().__init__(name, eType, **kwargs)

    def to_code(self):
        if self.required:
            return "{0}".format(self.name)
        if hasattr(self.eType, 'default_value'):
            default_value = self.eType.default_value
        else:
            default_value = None
        return "{0}={1}".format(self.name, default_value)


class ETypeParameter(ENamedElement):
    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)


class EGenericType(EObject):
    pass


class EClassifier(ENamedElement):
    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)

    @staticmethod
    def __isinstance__(self, instance=None):
        return (instance is None and
                (self is EClassifier or
                 isinstance(self, (EClassifier, MetaEClass)) or
                 getattr(self, '_staticEClass', False)))


class EDataType(EClassifier):
    # Must be completed
    # tuple is '(implem_type, use_type_as_factory, default_value)'
    javaTransMap = {'java.lang.String': (str, False, None),
                    'boolean': (bool, False, False),
                    'java.lang.Boolean': (bool, False, False),
                    'byte': (int, False, 0),
                    'short': (int, False, 0),
                    'int': (int, False, 0),
                    'long': (int, False, 0),
                    'float': (float, False, 0.0),
                    'java.lang.Short': (int, False, None),
                    'java.lang.Long': (int, False, None),
                    'java.lang.Float': (float, False, None),
                    'java.lang.Integer': (int, False, None),
                    'java.lang.Class': (type, False, None),
                    'java.lang.Object': (object, False, None),
                    'java.util.Map': (dict, True, None),
                    'java.util.Map$Entry': (dict, True, None),
                    'double': (float, False, 0.0),
                    'java.lang.Double': (float, False, None),
                    'char': (str, False, ''),
                    'java.lang.Character': (str, False, None),
                    'byte[]': (bytearray, True, None),
                    'java.lang.Byte': (int, False, None),
                    'java.util.Date': (datetime, False, None),
                    'org.eclipse.emf.common.util.EList': (list, True, None),
                    'org.eclipse.emf.ecore.util.FeatureMap': (dict,
                                                              True,
                                                              None),
                    'org.eclipse.emf.ecore.util.FeatureMap$Entry': (dict,
                                                                    True,
                                                                    None)}

    def __init__(self, name=None, eType=None, default_value=None,
                 from_string=None, to_string=None, instanceClassName=None,
                 type_as_factory=False, **kwargs):
        super().__init__(name, **kwargs)
        self.eType = eType
        self.type_as_factory = type_as_factory
        self._default_value = default_value
        if instanceClassName:
            self.instanceClassName = instanceClassName
        else:
            self._instanceClassName = None
        if from_string:
            self.from_string = from_string
        if to_string:
            self.to_string = to_string

    def from_string(self, value):
        return value

    def to_string(self, value):
        return str(value)

    def __instancecheck__(self, instance):
        return isinstance(instance, self.eType)

    @property
    def default_value(self):
        if self.type_as_factory:
            return self.eType()
        else:
            return self._default_value

    @default_value.setter
    def default_value(self, value):
        self._default_value = value

    @property
    def instanceClassName(self):
        return self._instanceClassName

    @instanceClassName.setter
    def instanceClassName(self, name):
        self._instanceClassName = name
        type, type_as_factory, default = self.javaTransMap.get(name, (object,
                                                                      True,
                                                                      None))
        self.eType = type
        self.type_as_factory = type_as_factory
        self.default_value = default

    def __repr__(self):
        etype = self.eType.__name__ if self.eType else None
        return '{0}({1})'.format(self.name, etype)


class EEnum(EDataType):
    def __init__(self, name=None, default_value=None, literals=None, **kwargs):
        super().__init__(name, eType=self, **kwargs)
        if literals:
            for i, lit_name in enumerate(literals):
                lit_name = '_' + lit_name if lit_name[:1].isnumeric() \
                                          else lit_name
                literal = EEnumLiteral(value=i, name=lit_name)
                self.eLiterals.append(literal)
                self.__setattr__(lit_name, literal)
        if default_value:
            self.default_value = default_value

    @property
    def default_value(self):
        return self.eLiterals[0] if self.eLiterals else None

    @default_value.setter
    def default_value(self, value):
        if value in self:
            literal = (value if isinstance(value, EEnumLiteral)
                       else self.getEEnumLiteral(value))
            literals = self.eLiterals
            i = literals.index(literal)
            literals.insert(0, literals.pop(i))
        else:
            raise AttributeError('Enumeration literal {} does not exist '
                                 'in {}'.format(value, self))

    def __contains__(self, key):
        if isinstance(key, EEnumLiteral):
            return key in self.eLiterals
        return any(lit for lit in self.eLiterals if lit.name == key)

    def __instancecheck__(self, instance):
        return instance in self

    def getEEnumLiteral(self, name=None, value=0):
        try:
            if name:
                return next(lit for lit in self.eLiterals if lit.name == name)
            return next(lit for lit in self.eLiterals if lit.value == value)
        except StopIteration:
            return None

    def from_string(self, value):
        return self.getEEnumLiteral(name=value)

    def __repr__(self):
        name = self.name or ''
        return '{}[{}]'.format(name, str(self.eLiterals))


class EEnumLiteral(ENamedElement):
    def __init__(self, name=None, value=0, **kwargs):
        super().__init__(name, **kwargs)
        self.value = value

    def __repr__(self):
        return '{0}={1}'.format(self.name, self.value)

    def __str__(self):
        return self.name


class EStructuralFeature(ETypedElement):
    def __init__(self, name=None, eType=None, changeable=True, volatile=False,
                 transient=False, unsettable=False, derived=False, **kwargs):
        super().__init__(name, eType, **kwargs)
        self.changeable = changeable
        self.volatile = volatile
        self.transient = transient
        self.unsettable = unsettable
        self.derived = derived
        self._name = name
        self._eternal_listener.append(self)

    def notifyChanged(self, notif):
        if notif.feature is ENamedElement.name:
            self._name = notif.new

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        name = self._name
        instance_dict = instance.__dict__
        if name not in instance_dict:
            if self.many:
                new_value = ECollection.create(instance, self)
            else:
                new_value = EValue(instance, self)
            instance_dict[name] = new_value
            return new_value._get()
        value = instance_dict[name]
        if type(value) is EValue:
            return value._get()
        else:
            return value

    def __set__(self, instance, value):
        name = self._name
        instance_dict = instance.__dict__
        if isinstance(value, ECollection):
            instance_dict[name] = value
            return
        if name not in instance_dict:
            if self.many:
                new_value = ECollection.create(instance, self)
            else:
                new_value = EValue(instance, self)
            instance_dict[name] = new_value
        previous_value = instance_dict[name]
        if isinstance(previous_value, ECollection):
            raise BadValueError(got=value, expected=previous_value.__class__)
        instance_dict[name]._set(value)

    def __delete__(self, instance):
        name = self._name
        value = getattr(instance, name)
        if self.many:
            value.clear()
        else:
            setattr(instance, name, self.get_default_value())

    def __repr__(self):
        eType = getattr(self, 'eType', None)
        name = getattr(self, 'name', None)
        return '<{0} {1}: {2}>'.format(self.__class__.__name__, name, eType)


class EAttribute(EStructuralFeature):
    def __init__(self, name=None, eType=None, default_value=None, iD=False,
                 **kwargs):
        super().__init__(name, eType, **kwargs)
        self.iD = iD
        self.default_value = default_value
        if self.default_value is None and isinstance(eType, EDataType):
            self.default_value = eType.default_value

    def get_default_value(self):
        if self.default_value is not None:
            return self.default_value
        elif self.eType is None:
            self.eType = ENativeType
            return object()
        return self.eType.default_value


class EReference(EStructuralFeature):
    def __init__(self, name=None, eType=None, containment=False,
                 eOpposite=None, **kwargs):
        super().__init__(name, eType, **kwargs)
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
    def __new__(cls, name=None, superclass=None, metainstance=None, **kwargs):
        if type(name) is not str:
            raise BadValueError(got=name, expected=str)
        instance = super().__new__(cls)
        if isinstance(superclass, tuple):
            [instance.eSuperTypes.append(x) for x in superclass]
        elif isinstance(superclass, EClass):
            instance.eSuperTypes.append(superclass)
        if metainstance:
            instance.python_class = metainstance
            instance.__name__ = metainstance.__name__
        else:
            def new_init(self, *args, **kwargs):
                for name, value in kwargs.items():
                    setattr(self, name, value)
            attr_dict = {
                'eClass': instance,
                '_staticEClass': instance._staticEClass,
                '__init__': new_init
            }
            instance.python_class = type(name,
                                         instance.__compute_supertypes(),
                                         attr_dict)
        instance.__name__ = name
        instance.supertypes_updater = EObserver()
        instance.supertypes_updater.notifyChanged = instance.__update
        instance._eternal_listener.append(instance.supertypes_updater)
        return instance

    def __init__(self, name=None, superclass=None, abstract=False,
                 metainstance=None, **kwargs):
        super().__init__(name, **kwargs)
        self.abstract = abstract

    def __call__(self, *args, **kwargs):
        if self.abstract:
            raise TypeError("Can't instantiate abstract EClass {0}"
                            .format(self.name))
        return self.python_class(*args, **kwargs)

    def __update(self, notif):
        # We do not update in case of static metamodel (could be changed)
        if getattr(self.python_class, '_staticEClass', False):
            return
        if notif.feature is EClass.eSuperTypes:
            new_supers = self.__compute_supertypes()
            self.python_class.__bases__ = new_supers
        elif notif.feature is EClass.eOperations:
            if notif.kind is Kind.ADD:
                self.__create_fun(notif.new)
            elif notif.kind is Kind.REMOVE:
                delattr(self.python_class, notif.old.name)
        elif notif.feature is EClass.eStructuralFeatures:
            if notif.kind is Kind.ADD:
                setattr(self.python_class, notif.new.name, notif.new)
            elif notif.kind is Kind.ADD_MANY:
                for x in notif.new:
                    setattr(self.python_class, x.name, x)
            elif notif.kind is Kind.REMOVE:
                delattr(self.python_class, notif.old.name)
        elif notif.feature is EClass.name and notif.kind is Kind.SET:
            self.python_class.__name__ = notif.new
            self.__name__ = notif.new

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
            if eSuperTypes and EObject.eClass in eSuperTypes:
                eSuperTypes.remove(EObject.eClass)
            return tuple(x.python_class for x in eSuperTypes)

    def __repr__(self):
        return '<{0} name="{1}">'.format(self.__class__.__name__, self.name)

    @property
    def eAttributes(self):
        return [x for x in self.eStructuralFeatures
                if isinstance(x, EAttribute)]

    @property
    def eReferences(self):
        return [x for x in self.eStructuralFeatures
                if isinstance(x, EReference)]

    def findEStructuralFeature(self, name):
        return next((f for f in self._eAllStructuralFeatures_gen()
                     if f.name == name),
                    None)

    def _eAllSuperTypes_gen(self):
        super_types = self.eSuperTypes
        for x in super_types:
            yield x
        for x in super_types:
            yield from x._eAllSuperTypes_gen()

    def eAllSuperTypes(self):
        return OrderedSet(self._eAllSuperTypes_gen())

    def _eAllStructuralFeatures_gen(self):
        for x in self.eStructuralFeatures:
            yield x
        for parent in self.eSuperTypes:
            yield from parent._eAllStructuralFeatures_gen()

    def eAllStructuralFeatures(self):
        return OrderedSet(self._eAllStructuralFeatures_gen())

    def eAllReferences(self):
        return set((x for x in self._eAllStructuralFeatures_gen()
                    if isinstance(x, EReference)))

    def eAllAttributes(self):
        return set((x for x in self._eAllStructuralFeatures_gen()
                    if isinstance(x, EAttribute)))

    def _eAllOperations_gen(self):
        for x in self.eOperations:
            yield x
        for parent in self.eSuperTypes:
            yield from parent._eAllOperations_gen()

    def eAllOperations(self):
        return OrderedSet(self._eAllOperations_gen())

    def findEOperation(self, name):
        return next((f for f in self._eAllOperations_gen() if f.name == name),
                    None)

    def __instancecheck__(self, instance):
        return isinstance(instance, self.python_class)


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
        return super().__call__(*args, **kwargs)


def EMetaclass(cls):
    """Class decorator for creating PyEcore metaclass."""
    superclass = cls.__bases__
    if not issubclass(cls, EObject):
        sclasslist = list(superclass)
        if object in superclass:
            index = sclasslist.index(object)
            sclasslist.insert(index, EObject)
            sclasslist.remove(object)
        else:
            sclasslist.insert(0, EObject)
        superclass = tuple(sclasslist)
    orig_vars = cls.__dict__.copy()
    slots = orig_vars.get('__slots__')
    if slots is not None:
        if isinstance(slots, str):
            slots = [slots]
        for slots_var in slots:
            orig_vars.pop(slots_var)
    orig_vars.pop('__dict__', None)
    orig_vars.pop('__weakref__', None)
    return MetaEClass(cls.__name__, superclass, orig_vars)


class EProxy(EObject):
    def __new__(cls, *args, **kwargs):
        return object.__new__(cls)

    def __init__(self, path=None, resource=None, wrapped=None, **kwargs):
        super().__init__(**kwargs)
        super().__setattr__('resolved', wrapped is not None)
        super().__setattr__('_wrapped', wrapped)
        super().__setattr__('_proxy_path', path)
        super().__setattr__('_proxy_resource', resource)
        super().__setattr__('_inverse_rels', set())

    def force_resolve(self):
        if self.resolved:
            return
        resource = self._proxy_resource
        decoders = resource._get_href_decoder(self._proxy_path)
        self._wrapped = decoders.resolve(self._proxy_path, resource)
        self._wrapped._inverse_rels.update(self._inverse_rels)
        self._inverse_rels = self._wrapped._inverse_rels
        self.resolved = True

    def delete(self, recursive=True):
        if recursive and self.resolved:
            [obj.delete() for obj in self.eAllContents()]

        seek = set(self._inverse_rels)
        if self.resolved:
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
        if name in ('_wrapped', '_proxy_path', '_proxy_resource', 'resolved',
                    'force_resolve', 'delete'):
            return super().__getattribute__(name)
        resolved = super().__getattribute__('resolved')
        if not resolved:
            if name in ('__class__', '_inverse_rels', '__name__'):
                return super().__getattribute__(name)
            resource = self._proxy_resource
            decoders = resource._get_href_decoder(self._proxy_path)
            decoded = decoders.resolve(self._proxy_path, resource)
            if not hasattr(decoded, '_inverse_rels'):
                self._wrapped = decoded.eClass
            else:
                self._wrapped = decoded
            self._wrapped._inverse_rels.update(self._inverse_rels)
            self._inverse_rels = self._wrapped._inverse_rels
            self.resolved = True
        return self._wrapped.__getattribute__(name)

    def __setattr__(self, name, value):
        if name in ('_wrapped', '_proxy_path', 'resolved', '_proxy_resource'):
            super().__setattr__(name, value)
            return
        resolved = self.resolved
        if not resolved:
            resource = self._proxy_resource
            decoders = resource._get_href_decoder(self._proxy_path)
            decoded = decoders.resolve(self._proxy_path, resource)
            if not hasattr(decoded, '_inverse_rels'):
                self._wrapped = decoded.eClass
            else:
                self._wrapped = decoded
            self.resolved = True
        self._wrapped.__setattr__(name, value)

    def __instancecheck__(self, instance):
        self.force_resolve()
        return self._wrapped.__instancecheck__(instance)


def abstract(cls):
    cls.eClass.abstract = True
    return cls


# meta-meta level
EString = EDataType('EString', str)
ENamedElement.name = EAttribute('name', EString)
ENamedElement.name._isset.add(ENamedElement.name)  # special case
EString._isset.add(ENamedElement.name)  # special case

EBoolean = EDataType('EBoolean', bool, False,
                     to_string=lambda x: str(x).lower(),
                     from_string=lambda x: x in ['True', 'true'])
EBooleanObject = EDataType('EBooleanObject', bool,
                           to_string=lambda x: str(x).lower(),
                           from_string=lambda x: x in ['True', 'true'])
EInteger = EDataType('EInteger', int, 0, from_string=lambda x: int(x))
EInt = EDataType('EInt', int, 0, from_string=lambda x: int(x))
ELong = EDataType('ELong', int, 0, from_string=lambda x: int(x))
ELongObject = EDataType('ELongObject', int, from_string=lambda x: int(x))
EIntegerObject = EDataType('EIntegerObject', int, from_string=lambda x: int(x))
EBigInteger = EDataType('EBigInteger', int, from_string=lambda x: int(x))
EDouble = EDataType('EDouble', float, 0.0, from_string=lambda x: float(x))
EDoubleObject = EDataType('EDoubleObject', float,
                          from_string=lambda x: float(x))
EFloat = EDataType('EFloat', float, 0.0, from_string=lambda x: float(x))
EFloatObject = EDataType('EFloatObject', float, from_string=lambda x: float(x))
EStringToStringMapEntry = EDataType('EStringToStringMapEntry', dict,
                                    type_as_factory=True)
EFeatureMapEntry = EDataType('EFeatureMapEntry', dict, type_as_factory=True)
EDiagnosticChain = EDataType('EDiagnosticChain', str)
ENativeType = EDataType('ENativeType', object)
EJavaObject = EDataType('EJavaObject', object)
EDate = EDataType('EDate', datetime)
EBigDecimal = EDataType('EBigDecimal', Decimal,
                        from_string=lambda x: Decimal(x))
EByte = EDataType('EByte', bytes)
EByteObject = EDataType('EByteObject', bytes)
EByteArray = EDataType('EByteArray', bytearray)
EChar = EDataType('EChar', str)
ECharacterObject = EDataType('ECharacterObject', str)
EShort = EDataType('EShort', int, from_string=lambda x: int(x))
EJavaClass = EDataType('EJavaClass', type)


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
ENamedElement.name._isset.add(ETypedElement.eType)  # special case

EStructuralFeature.changeable = EAttribute('changeable', EBoolean,
                                           default_value=True)
EStructuralFeature.volatile = EAttribute('volatile', EBoolean)
EStructuralFeature.transient = EAttribute('transient', EBoolean)
EStructuralFeature.unsettable = EAttribute('unsettable', EBoolean)
EStructuralFeature.derived = EAttribute('derived', EBoolean)
EStructuralFeature.defaultValueLiteral = EAttribute('defaultValueLiteral',
                                                    EString)

EAttribute.iD = EAttribute('iD', EBoolean)

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

EDataType.instanceClassName_ = EAttribute('instanceClassName', EString)
EDataType.serializable = EAttribute('serializable', EBoolean)

EClass.abstract = EAttribute('abstract', EBoolean)
EClass.eStructuralFeatures = EReference('eStructuralFeatures',
                                        EStructuralFeature,
                                        upper=-1, containment=True)
EClass.eAttributes_ = EReference('eAttributes', EAttribute,
                                 upper=-1, derived=True)
EClass.eReferences_ = EReference('eReferences', EReference,
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
EReference.eOpposite_ = EReference('eOpposite', EReference)
EReference.resolveProxies = EAttribute('resolveProxies', EBoolean)

EEnum.eLiterals = EReference('eLiterals', EEnumLiteral, upper=-1,
                             containment=True)

EEnumLiteral.eEnum = EReference('eEnum', EEnum, eOpposite=EEnum.eLiterals)
EEnumLiteral.name = EAttribute('name', EString)
EEnumLiteral.value = EAttribute('value', EInteger)
EEnumLiteral.literal = EAttribute('literal', EString)

EOperation.eContainingClass = EReference('eContainingClass', EClass,
                                         eOpposite=EClass.eOperations)
EOperation.eParameters = EReference('eParameters', EParameter, upper=-1,
                                    containment=True)
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
Core.register_classifier(EObject, promote=True)
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
Core.register_classifier(EStructuralFeature, promote=True)
Core.register_classifier(EAttribute, promote=True)
Core.register_classifier(EReference, promote=True)
Core.register_classifier(EClass, promote=True)
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
Core.register_classifier(EFeatureMapEntry)
Core.register_classifier(EDiagnosticChain)
Core.register_classifier(ENativeType)
Core.register_classifier(EJavaObject)
Core.register_classifier(EDate)
Core.register_classifier(EBigDecimal)
Core.register_classifier(EBooleanObject)
Core.register_classifier(ELongObject)
Core.register_classifier(EByte)
Core.register_classifier(EByteObject)
Core.register_classifier(EByteArray)
Core.register_classifier(EChar)
Core.register_classifier(ECharacterObject)
Core.register_classifier(EShort)
Core.register_classifier(EJavaClass)


__all__ = ['EObject', 'EModelElement', 'ENamedElement', 'EAnnotation',
           'EPackage', 'EGenericType', 'ETypeParameter', 'ETypedElement',
           'EClassifier', 'EDataType', 'EEnum', 'EEnumLiteral', 'EParameter',
           'EOperation', 'EClass', 'EStructuralFeature', 'EAttribute',
           'EReference', 'EString', 'EBoolean', 'EInteger',
           'EStringToStringMapEntry', 'EDiagnosticChain', 'ENativeType',
           'EJavaObject', 'abstract', 'MetaEClass', 'EList', 'ECollection',
           'EOrderedSet', 'ESet', 'EcoreUtils', 'BadValueError', 'EDouble',
           'EDoubleObject', 'EBigInteger', 'EInt', 'EIntegerObject', 'EFloat',
           'EFloatObject', 'ELong', 'EProxy', 'EBag', 'EFeatureMapEntry',
           'EDate', 'EBigDecimal', 'EBooleanObject', 'ELongObject', 'EByte',
           'EByteObject', 'EByteArray', 'EChar', 'ECharacterObject',
           'EShort', 'EJavaClass', 'EMetaclass']
