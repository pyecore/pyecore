import sys
from inspect import getmembers, isclass


nsPrefix = 'ecore'
nsURI = 'http://www.eclipse.org/emf/2002/Ecore'


def getEClassifier(name, searchspace=None):
    searchspace = searchspace if searchspace else eClassifiers
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
        elif isinstance(_type, EEnum):
            return obj in _type
        elif isinstance(_type, EDataType) or isinstance(_type, EAttribute):
            return isinstance(obj, _type.eType)
        elif isinstance(_type, EClass):
            if isinstance(obj, EObject):
                return obj.eClass is _type \
                       or _type in obj.eClass.eAllSuperTypes()
            return False
        return isinstance(obj, _type)


class Core(object):
    def getattr(self, name):
        ex = None
        try:
            return object.__getattribute__(self, name)
        except AttributeError as e:
            ex = e
        feature = self.eClass.findEStructuralFeature(name)
        if not feature:
            raise ex

        if feature.many:
            new_list = EList(self, feature)
            self.__setattr__(name, new_list)
            return new_list
        else:
            default_value = None
            if hasattr(feature.eType, 'default_value'):
                default_value = feature.eType.default_value
            if hasattr(feature, 'default_value'):
                default_value = feature.default_value
            self.__setattr__(name, default_value)
            return default_value

    def setattr(self, name, value):
        feat = self.eClass.findEStructuralFeature(name)
        if not feat:
            object.__setattr__(self, name, value)
            return

        if feat.many and not isinstance(value, EList):
            raise BadValueError(got=value, expected=feat.eType)
        elif not feat.many and not EcoreUtils.isinstance(value, feat.eType):
            raise BadValueError(got=value, expected=feat.eType)

        try:
            previous_value = object.__getattribute__(self, feat.name)
        except AttributeError:
            previous_value = None

        object.__setattr__(self, name, value)
        if self._isready:
            self._isset.append(name)
        if self._isready and isinstance(feat, EReference):
            if feat.containment and isinstance(value, EObject):
                value._container = self
            elif feat.containment and not value and previous_value:
                previous_value._container = None
            if feat.eOpposite and isinstance(value, EObject):
                eOpposite = feat.eOpposite
                if eOpposite.many:
                    value.__getattr__(eOpposite.name)  # force resolve
                    object.__getattribute__(value, eOpposite.name).append(self)
                else:
                    object.__setattr__(value, eOpposite.name, self)
            elif feat.eOpposite and value is None:
                eOpposite = feat.eOpposite
                if previous_value and eOpposite.many:
                    object.__getattribute__(previous_value, eOpposite.name) \
                          .remove(self)
                elif previous_value:
                    object.__setattr__(previous_value, eOpposite.name, None)

    def _promote(cls, abstract=False):
        cls.eClass = EClass(cls.__name__)
        cls.eClass.abstract = abstract
        cls._staticEClass = True
        # init super types
        for _cls in cls.__bases__:
            if _cls is not EObject:
                cls.eClass.eSuperTypes.append(_cls.eClass)
        # init eclass by reflection
        for k, v in cls.__dict__.items():
            if isinstance(v, EAttribute):
                if not v.name:
                    v.name = k
                cls.eClass.eAttributes.append(v)
            elif isinstance(v, EReference):
                if not v.name:
                    v.name = k
                cls.eClass.eReferences.append(v)

    def compute_eclass(module_name):
        module = sys.modules[module_name]

        def is_valid_eclass(_class):
            return isclass(_class) and _class.__module__ is module_name
        return {k: v for k, v in getmembers(module, is_valid_eclass)}


class EObject(object):
    def __init__(self):
        self.__initmetattr__()
        self.__subinit__()

    def __subinit__(self):
        self._xmiid = None
        self._isset = []
        self._container = None
        self._isready = False

    def __initmetattr__(self, _super=None):
        _super = _super if _super else self.__class__
        if _super is EObject:
            return
        for key, value in _super.__dict__.items():
            if isinstance(value, EAttribute):
                self.__setattr__(key, value)
            elif isinstance(value, EReference):
                if value.many:
                    self.__setattr__(key, EList(self, value))
                else:
                    self.__setattr__(key, None)
        for super_class in _super.__bases__:
            super_class.__initmetattr__(self, super_class)

    def eContainer(self):
        return self._container


class EList(list):
    def __init__(self, owner, efeature=None):
        super().__init__()
        self._owner = owner
        self._efeature = efeature

    def check(self, value):
        if not EcoreUtils.isinstance(value, self._efeature.eType):
            raise BadValueError(value, self._efeature.eType)

    def _update_container(self, value, previous_value=None):
        if not isinstance(self._efeature, EReference):
            return
        if self._efeature.containment and not previous_value:
            value._container = self._owner
        elif self._efeature.containment and previous_value:
            previous_value._container = value

    def _update_opposite(self, owner, new_value, remove=False):
        if not isinstance(self._efeature, EReference):
            return
        eOpposite = self._efeature.eOpposite
        if eOpposite:
            if eOpposite.many and not remove:
                owner.__getattr__(eOpposite.name)  # force resolve
                object.__getattribute__(owner, eOpposite.name) \
                      .append(new_value, False)
            elif eOpposite.many and remove:
                object.__getattribute__(owner, eOpposite.name) \
                      .remove(new_value, False)
            else:
                object.__setattr__(owner, eOpposite.name,
                                   None if remove else new_value)

    def append(self, value, update_opposite=True):
        self.check(value)
        if update_opposite:
            self._update_container(value)
            self._update_opposite(value, self._owner)
        list.append(self, value)

    def extend(self, sublist):
        all(self.check(x) for x in sublist)
        for x in sublist:
            self._update_container(x)
            self._update_opposite(x, self._owner)
        list.extend(self, sublist)

    def remove(self, value, update_opposite=True):
        if update_opposite:
            self._update_container(None, previous_value=value)
            self._update_opposite(value, self._owner, remove=True)
        list.remove(self, value)

    # for Python2 compatibility, in Python3, __setslice__ is deprecated
    def __setslice__(self, i, j, y):
        all(self.check(x) for x in y)
        list.__setslice__(self, i, j, y)

    def __setitem__(self, i, y):
        self.check(y)
        self._update_container(y)
        self._update_opposite(y, self._owner)
        list.__setitem__(self, i, y)

    def select(self, f):
        return [x for x in self if f(x)]

    def reject(self, f):
        return [x for x in self if not f(x)]


class EModelElement(EObject):
    def __init__(self):
        super().__init__()


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
        self.lowerBound = lower
        self.upperBound = upper
        self.ordered = ordered
        self.unique = unique
        self.required = required

    @property
    def upper(self):
        return self.upperBound

    @upper.setter
    def upper(self, value):
        self.upperBound = value

    @property
    def lower(self):
        return self.lowerBound

    @lower.setter
    def lower(self, value):
        self.lowerBound = value

    @property
    def many(self):
        return self.upperBound > 1 or self.upperBound < 0


class EOperation(ETypedElement):
    def __init__(self, name, eType=None, params=None, exceptions=None):
        super().__init__(name, eType)
        if params:
            for param in params:
                self.eParameters.append(param)
        if exceptions:
            for exception in exceptions:
                self.eExceptions.append(exception)


class EParameter(ETypedElement):
    def __init__(self, name, eType=None):
        super().__init__(name, eType)


class EClassifier(ENamedElement):
    def __init__(self, name=None):
        super().__init__(name)


class EDataType(EClassifier):
    def __init__(self, name=None, eType=None, default_value=None):
        super().__init__(name)
        self.eType = eType
        self.default_value = default_value

    def __repr__(self):
        return '{0}({1})'.format(self.name, self.eType.__name__)


class EEnum(EDataType):
    def __init__(self, name, default_value=None, literals=None):
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
        return self.name + str(self.eLiterals)


class EEnumLiteral(ENamedElement):
    def __init__(self, value, name):
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


class EAttribute(EStructuralFeature):
    def __init__(self, name=None, eType=None, default_value=None,
                 lower=0, upper=1, changeable=True, derived=False):
        super().__init__(name, eType, lower=lower, upper=upper,
                         derived=derived, changeable=changeable)
        self.default_value = default_value
        if not self.default_value and isinstance(eType, EDataType):
            self.default_value = eType.default_value


class EReference(EStructuralFeature):
    def __init__(self, name=None, eType=None, lower=0, upper=1,
                 containment=False, eOpposite=None, ordered=True, unique=True):
        super().__init__(name, eType, ordered, unique, lower=lower,
                         upper=upper)
        self.containment = containment
        self.eOpposite = eOpposite
        if eOpposite:
            eOpposite.eOpposite = self
        if not isinstance(eType, EClass) and hasattr(eType, 'eClass'):
            self.eType = eType.eClass


class EClass(EClassifier):
    def __init__(self, name=None, superclass=None, abstract=False):
        super().__init__(name)
        self.abstract = abstract
        if isinstance(superclass, tuple):
            [self.eSuperTypes.append(x) for x in superclass]
        elif isinstance(superclass, EClass):
            self.eSuperTypes.append(superclass)
        self.__metainstance = type(self.name, (EObject,), {
                                    'eClass': self,
                                    '__getattr__': Core.getattr,
                                    '__setattr__': Core.setattr
                                })

    def __call__(self, *args, **kwargs):
        if self.abstract:
            raise TypeError("Can't instantiate abstract EClass {0}"
                            .format(self.name))
        obj = self.__metainstance()
        obj._isready = True
        return obj

    def __repr__(self):
        return '<EClass name="{0}">'.format(self.name)

    @property
    def eStructuralFeatures(self):
        return self.eAttributes + self.eReferences

    def findEStructuralFeature(self, name):
        return next(
                (f for f in self.eAllStructuralFeatures() if f.name == name),
                None)

    def eAllSuperTypes(self, building=None):
        if isinstance(self, type):
            return [x.eClass for x in self.mro() if x is not object and
                    x is not self]
        if not self.eSuperTypes:
            return []
        building = building if building else []
        stypes = []
        [stypes.append(x) for x in self.eSuperTypes if x not in building]
        for ec in self.eSuperTypes:
            stypes.extend(ec.eAllSuperTypes(stypes))
        return stypes

    def eAllStructuralFeatures(self):
        feats = self.eStructuralFeatures
        [feats.extend(x.eStructuralFeatures) for x in self.eAllSuperTypes()]
        return feats


EClass.eClass = EClass


# Meta methods for static EClass
class MetaEClass(type):
    def __init__(cls, name, bases, nmspc):
        super().__init__(name, bases, nmspc)
        cls.__getattr__ = Core.getattr
        cls.__setattr__ = Core.setattr
        Core._promote(cls)

    def __call__(cls, *args, **kwargs):
        if cls.eClass.abstract:
            raise TypeError("Can't instantiate abstract EClass {0}"
                            .format(cls.eClass.name))
        obj = type.__call__(cls, *args, **kwargs)
        # init instances by reflection
        EObject.__subinit__(obj)
        for efeat in reversed(obj.eClass.eAllStructuralFeatures()):
            if isinstance(efeat, EAttribute):
                obj.__setattr__(efeat.name, efeat.default_value)
            elif efeat.many:
                obj.__setattr__(efeat.name, EList(obj, efeature=efeat))
            else:
                obj.__setattr__(efeat.name, None)
        obj._isready = True
        return obj


def abstract(cls):
    cls.eClass.abstract = True
    return cls


# meta-meta level
EString = EDataType('EString', str)
EBoolean = EDataType('EBoolean', bool, False)
EInteger = EDataType('EInteger', int, 0)
EStringToStringMapEntry = EDataType('EStringToStringMapEntry', dict, {})

EModelElement.eAnnotations = EReference('eAnnotations', EAnnotation, upper=-1,
                                        containment=True)
EAnnotation.eModelElement = EReference('eModelElement', EModelElement,
                                       eOpposite=EModelElement.eAnnotations)
EAnnotation.source = EAttribute('source', EString)
EAnnotation.details = EAttribute('details', EStringToStringMapEntry)

ENamedElement.name = EAttribute('name', EString)

ETypedElement.ordered = EAttribute('ordered', EBoolean, default_value=True)
ETypedElement.unique = EAttribute('unique', EBoolean, default_value=True)
ETypedElement.lower = EAttribute('lower', EInteger, derived=True)
ETypedElement.lowerBound = EAttribute('lowerBound', EInteger)
ETypedElement.upper = EAttribute('upper', EInteger, default_value=1,
                                                    derived=True)
ETypedElement.upperBound = EAttribute('upperBound', EInteger, default_value=1)
ETypedElement.required = EAttribute('required', EBoolean)
ETypedElement.eType = EReference('eType', EClassifier)
ETypedElement.default_value = EAttribute('default_value', type)

EStructuralFeature.changeable = EAttribute('changeable', EBoolean,
                                           default_value=True)
EStructuralFeature.volatile = EAttribute('volatile', EBoolean)
EStructuralFeature.transient = EAttribute('transient', EBoolean)
EStructuralFeature.unsettable = EAttribute('unsettable', EBoolean)
EStructuralFeature.derived = EAttribute('derived', EBoolean)


EPackage.nsURI = EAttribute('nsURI', EString)
EPackage.nsPrefix = EAttribute('nsPrefix', EString)
EPackage.eClassifiers = EReference('eClassifiers', EClass, upper=-1,
                                   containment=True)
EPackage.eSubpackages = EReference('eSubpackages', EPackage, upper=-1,
                                   containment=True)
EPackage.eSuperPackage = EReference('eSuperPackage', EPackage, lower=1,
                                    eOpposite=EPackage.eSubpackages)

EClassifier.ePackage = EReference('ePackage', EPackage,
                                  eOpposite=EPackage.eClassifiers)

EClass.abstract = EAttribute('abstract', EBoolean)
EClass.eAttributes = EReference('eAttributes', EAttribute, upper=-1,
                                containment=True)
EClass.eReferences = EReference('eReferences', EReference, upper=-1,
                                containment=True)
EClass.eSuperTypes = EReference('eSuperTypes', EClass, upper=-1)

EAttribute.eContainingClass = EReference('eContainingClass', EClass,
                                         eOpposite=EClass.eAttributes)

EReference.containment = EAttribute('containment', EBoolean)
EReference.eOpposite = EReference('eOpposite', EReference)
EReference.eContainingClass = EReference('eContainingClass', EClass,
                                         eOpposite=EClass.eReferences)

EEnum.eLiterals = EReference('eLiterals', EEnumLiteral, upper=-1,
                             containment=True)

EEnumLiteral.eEnum = EReference('eEnum', EEnum, eOpposite=EEnum.eLiterals)

EOperation.eParameters = EReference('eParameters', EParameter, upper=-1)
EOperation.eExceptions = EReference('eExceptions', EClassifier, upper=-1)

EParameter.eOperation = EReference('eOperation', EOperation)

Core._promote(EModelElement)
Core._promote(ENamedElement)
Core._promote(EAnnotation)
Core._promote(EPackage)
Core._promote(ETypedElement)
Core._promote(EDataType)
Core._promote(EClassifier)
Core._promote(EEnum)
Core._promote(EEnumLiteral)
Core._promote(EParameter)
Core._promote(EOperation)
Core._promote(EClass)
Core._promote(EStructuralFeature)
Core._promote(EAttribute)
Core._promote(EReference)

# We compute all the Metaclasses from the current module (EPackage-alike)
eClassifiers = Core.compute_eclass(__name__)
