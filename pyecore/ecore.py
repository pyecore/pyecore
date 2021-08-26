# -*- coding: future_fstrings -*-
"""This module is the heart of PyEcore. It defines all the basic concepts that
are common to EMF-Java and PyEcore (EObject/EClass...).
It defines the basic classes and behavior for PyEcore implementation:

* EObject
* EPackage
* EClass
* EAttribute
* EReference
* EDataType

These concepts are enough if dynamic metamodel instance are handled (code
generation is not required).

In addition, ``@EMetaclass`` annotation and ``MetaEClass`` metaclass are
used for static metamodels definition.
"""
import sys
import keyword
import inspect
from decimal import Decimal
from datetime import datetime
from ordered_set import OrderedSet
from weakref import WeakSet
from RestrictedPython import compile_restricted, safe_builtins
from .notification import ENotifer, Kind
from .innerutils import ignored, javaTransMap, parse_date


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


class Core(object):
    @staticmethod
    def _promote(rcls, abstract=False):
        rcls.eClass = EClass(rcls.__name__, metainstance=rcls)
        rcls.eClass.abstract = abstract
        rcls._staticEClass = True
        # init super types
        eSuperTypes_add = rcls.eClass.eSuperTypes.append
        for _cls in rcls.__bases__:
            if _cls is EObject:
                continue
            with ignored(Exception):
                eSuperTypes_add(_cls.eClass)
        # init eclass by reflection
        eStructuralFeatures_add = rcls.eClass.eStructuralFeatures.append
        eTypeParameters_add = rcls.eClass.eTypeParameters.add
        for k, feature in rcls.__dict__.items():
            if isinstance(feature, EStructuralFeature):
                if not feature.name:
                    feature.name = k
                eStructuralFeatures_add(feature)
            elif isinstance(feature, ETypeParameter):
                if not feature.name:
                    feature.name = k
                eTypeParameters_add(feature)
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
                rcls.eClass.eOperations.append(operation)

    @classmethod
    def register_classifier(cls, rcls, abstract=False, promote=False):
        if promote:
            cls._promote(rcls, abstract)
        epackage = sys.modules[rcls.__module__]
        if not hasattr(epackage, 'eClassifiers'):
            eclassifs = {}
            epackage.eClassifiers = eclassifs
            epackage.getEClassifier = \
                lambda x: getEClassifier(x, searchspace=eclassifs)
        if not hasattr(epackage, 'eClass'):
            pack_name = (epackage.__name__ if epackage.__name__ != '__main__'
                         else 'default_package')
            epackage.eClass = EPackage(name=pack_name,
                                       nsPrefix=pack_name,
                                       nsURI=f'http://{pack_name}/')
        if not hasattr(epackage, 'eURIFragment'):
            epackage.eURIFragment = eURIFragment
        cname = rcls.name if isinstance(rcls, EClassifier) else rcls.__name__
        epackage.eClassifiers[cname] = rcls
        if isinstance(rcls, EDataType):
            epackage.eClass.eClassifiers.append(rcls)
            rcls._container = epackage
        else:
            epackage.eClass.eClassifiers.append(rcls.eClass)
            rcls.eClass._container = epackage


class Metasubinstance(type):
    def __subclasscheck__(cls, other):
        if isinstance(other, EClass):
            other = other.python_class
        return type.__subclasscheck__(cls, other)


# Meta methods for static EClass
class MetaEClass(Metasubinstance):
    def __init__(cls, name, bases, nmspc):
        super().__init__(name, bases, nmspc)
        Core.register_classifier(cls, promote=True)
        cls._staticEClass = True

    def __call__(cls, *args, **kwargs):
        if cls.eClass.abstract:
            raise TypeError("Can't instantiate "
                            f"abstract EClass {cls.eClass.name}")
        return super().__call__(*args, **kwargs)


class EObject(ENotifer, metaclass=Metasubinstance):
    _staticEClass = True
    _instances = WeakSet()

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        instance._internal_id = None
        instance._isset = set()
        instance._container = None
        instance._containment_feature = None
        instance._eresource = None
        instance.listeners = []
        instance._eternal_listener = []
        instance._inverse_rels = set()
        instance._staticEClass = False
        cls._instances.add(instance)
        return instance

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def allInstances(cls, resources=None):
        if resources:
            yield from (x for x in cls._instances
                        if isinstance(x, cls) and x.eResource in resources)
        else:
            yield from (x for x in cls._instances if isinstance(x, cls))

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
        try:
            return self._container.eResource
        except AttributeError:
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
            for obj in self.eAllContents():
                obj.delete()
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
            if not feature.containment or feature.derived:
                continue
            if feature.many:
                values = self.__getattribute__(feature.name)
            else:
                values = [self.__getattribute__(feature.name)]
            children.extend((x for x in values if x))
        return children

    def eAllContents(self):
        contents = self.eContents
        yield from contents
        for x in contents:
            yield from x.eAllContents()

    def eURIFragment(self):
        if not self.eContainer():
            if not self.eResource or len(self.eResource.contents) == 1:
                return '/'
            else:
                return f'/{self.eResource.contents.index(self)}'
        feat = self.eContainmentFeature()
        parent = self.eContainer()
        name = feat.name
        if feat.many:
            index = parent.__getattribute__(name).index(self)
            return f'{parent.eURIFragment()}/@{name}.{index}'
        else:
            return f'{parent.eURIFragment()}/@{name}'

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


class EModelElement(EObject):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def eURIFragment(self):
        if not self.eContainer():
            if not self.eResource or len(self.eResource.contents) == 1:
                return '#/'
            else:
                return f'#/{self.eResource.contents.index(self)}'
        parent = self.eContainer()
        if hasattr(self, 'name'):
            return f'{parent.eURIFragment()}/{self.name}'
        else:
            return super().eURIFragment()

    def getEAnnotation(self, source):
        """Return the annotation with a matching source attribute."""
        return next((a for a in self.eAnnotations if a.source == source), None)


class EAnnotation(EModelElement):
    def __init__(self, source=None, **kwargs):
        super().__init__(**kwargs)
        self.source = source
        self.details = {}


class ENamedElement(EModelElement):
    def __init__(self, name=None, **kwargs):
        super().__init__(**kwargs)
        self.name = name


class SpecialEPackage(Metasubinstance):
    def __instancecheck__(cls, instance):
        if inspect.ismodule(instance) and hasattr(instance, 'nsURI'):
            return True
        return type.__instancecheck__(cls, instance)


class EPackage(ENamedElement, metaclass=SpecialEPackage):
    def __init__(self, name=None, nsURI=None, nsPrefix=None, **kwargs):
        super().__init__(name, **kwargs)
        self.nsURI = nsURI
        self.nsPrefix = nsPrefix

    def getEClassifier(self, name):
        return next((c for c in self.eClassifiers if c.name == name), None)

    # @staticmethod
    # def __isinstance__(self, instance=None):
    #     return (instance is None
    #             and (isinstance(self, EPackage)
    #                  or inspect.ismodule(self) and hasattr(self, 'nsURI')))


class ETypedElement(ENamedElement):
    def __init__(self, name=None, eType=None, ordered=True, unique=True,
                 lower=0, upper=1, required=False, eGenericType=None,
                 **kwargs):
        super().__init__(name, **kwargs)
        self.eType = eType
        self.lowerBound = int(lower)
        self.upperBound = int(upper)
        self.ordered = ordered
        self.unique = unique
        self.required = required
        if eGenericType:
            self.eGenericType = eGenericType
        self._many_cache = self._compute_many()
        self._eternal_listener.append(self)

    def _compute_many(self):
        upper = self.upperBound
        return upper < 0 or upper > 1

    def notifyChanged(self, notif):
        if notif.feature is ETypedElement.upperBound:
            self._many_cache = self._compute_many()

    @property
    def upper(self):
        return self.upperBound

    @property
    def lower(self):
        return self.lowerBound

    @property
    def many(self):
        return self._many_cache


class EOperation(ETypedElement):
    def __init__(self, name=None, eType=None, params=None, exceptions=None,
                 **kwargs):
        super().__init__(name, eType, **kwargs)
        if params:
            self.eParameters.extend(params)
        if exceptions:
            self.eExceptions.extend(exceptions)

    def normalized_name(self):
        name = self.name
        if keyword.iskeyword(name):
            name = name + '_'
        return name

    def to_code(self):
        parameters = [x.to_code() for x in self.eParameters]
        if len(parameters) == 0 or parameters[0] != 'self':
            parameters.insert(0, 'self')
        norm_name = self.normalized_name()
        parameters = ', '.join(parameters)
        return f"""def {norm_name}({parameters}):
        raise NotImplementedError('Method {norm_name}({parameters}) is not yet implemented')
        """ # noqa


class EParameter(ETypedElement):
    def __init__(self, name=None, eType=None, **kwargs):
        super().__init__(name, eType, **kwargs)

    def to_code(self):
        if self.required:
            return f"{self.name}"
        default_value = getattr(self.eType, 'default_value', None)
        return f"{self.name}={default_value}"


class ETypeParameter(ENamedElement):
    def __init__(self, name=None, eBounds=None, **kwargs):
        super().__init__(name, **kwargs)
        if eBounds:
            self.eBounds.extend(eBounds)

    def raw_types(self):
        raw_types = tuple(x.eRawType for x in self.eBounds)
        if not raw_types:
            raw_types = object
        return raw_types

    def __instancecheck__(self, instance):
        raw_types = self.raw_types()
        return isinstance(instance, raw_types)

    def __str__(self):
        raw_types = self.raw_types()
        return (f'<{self.__class__.__name__}[{raw_types}] object '
                f'at {hex(id(self))}>')


class EGenericType(EObject):
    def __init__(self, eTypeParameter=None, eClassifier=None, **kwargs):
        super().__init__(**kwargs)
        self.eTypeParameter = eTypeParameter
        self.eClassifier = eClassifier

    @property
    def eRawType(self):
        return self.eClassifier or self.eTypeParameter


# class SpecialEClassifier(Metasubinstance):
#     def __instancecheck__(cls, instance):
#         if cls is not EClassifier:
#             return type.__instancecheck__(cls, instance)
#         return isinstance(instance, Metasubinstance) or \
#               isinstance(instance, (EClass, EDataType, EPackage))


class EClassifier(ENamedElement):
    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)

    @staticmethod
    def __isinstance__(self, instance=None):
        return (instance is None
                and (self is EClassifier
                     or isinstance(self, (EClassifier, MetaEClass))
                     or getattr(self, '_staticEClass', False)))


class EDataType(EClassifier):
    transmap = javaTransMap

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
            self.instanceClassName_ = None
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
        return self.instanceClassName_

    @instanceClassName.setter
    def instanceClassName(self, name):
        self.instanceClassName_ = name
        default_type = (object, True, None)
        type_, type_as_factory, default = self.transmap.get(name, default_type)
        self.eType = type_
        self.type_as_factory = type_as_factory
        self.default_value = default

    def __repr__(self):
        etype = self.eType.__name__ if self.eType else None
        return f'{self.name}({etype})'


class EEnum(EDataType):
    def __init__(self, name=None, default_value=None, literals=None, **kwargs):
        super().__init__(name, eType=self, **kwargs)
        self._eternal_listener.append(self)
        if literals:
            for i, lit_name in enumerate(literals):
                lit_name = '_' + lit_name if lit_name[:1].isnumeric() \
                                          else lit_name
                literal = EEnumLiteral(value=i, name=lit_name)
                self.eLiterals.append(literal)
        if default_value:
            self.default_value = default_value

    def notifyChanged(self, notif):
        if notif.feature is EEnum.eLiterals:
            if notif.kind is Kind.ADD:
                literal = notif.new
                self.__setattr__(literal.name, literal)
            elif notif.kind is Kind.REMOVE:
                literal = notif.old
                del self.__dict__[literal.name]

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
            raise AttributeError(f'Enumeration literal {value} does not exist '
                                 f'in {self}')

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
        return f'{name}[{self.eLiterals}]'


class EEnumLiteral(ENamedElement):
    def __init__(self, name=None, value=0, **kwargs):
        super().__init__(name, **kwargs)
        self.value = value

    def __repr__(self):
        return f'{self.name}={self.value}'

    def __str__(self):
        return self.name


class EStructuralFeature(ETypedElement):
    def __init__(self, name=None, eType=None, changeable=True, volatile=False,
                 transient=False, unsettable=False, derived=False,
                 derived_class=None, **kwargs):
        super().__init__(name, eType, **kwargs)
        self.changeable = changeable
        self.volatile = volatile
        self.transient = transient
        self.unsettable = unsettable
        self.derived = derived
        self.derived_class = derived_class or ECollection
        self._name = name
        self._eType = eType

    def notifyChanged(self, notif):
        super().notifyChanged(notif)
        if notif.feature is ENamedElement.name:
            self._name = notif.new
        if notif.feature is ETypedElement.eType:
            self._eType = notif.new

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        name = self._name
        instance_dict = instance.__dict__
        if name in instance_dict:
            value = instance_dict[name]
            try:
                return value._get()
            except AttributeError:
                return value
        if self.many:
            new_value = self.derived_class.create(instance, self)
        else:
            new_value = EValue(instance, self)
        instance_dict[name] = new_value
        return new_value._get()

    def __set__(self, instance, value):
        name = self._name
        instance_dict = instance.__dict__
        if name not in instance_dict:
            if self.many:
                new_value = self.derived_class.create(instance, self)
            else:
                new_value = EValue(instance, self)
            instance_dict[name] = new_value
            previous_value = new_value
        else:
            previous_value = instance_dict[name]
        if isinstance(previous_value, ECollection):
            if value is previous_value:
                return
            if value is not previous_value and isinstance(value, ECollection):
                raise AttributeError('Cannot reafect an ECollection with '
                                     'another one, even if compatible')
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
        return f'<{self.__class__.__name__} {name}: {eType}>'


class EAttribute(EStructuralFeature):
    def __init__(self, name=None, eType=None, default_value=None, iD=False,
                 defaultValueLiteral=None, **kwargs):
        super().__init__(name, eType, **kwargs)
        self.iD = iD
        self.default_value = default_value
        self.defaultValueLiteral = defaultValueLiteral
        if default_value is None and isinstance(eType, EDataType):
            self.default_value = eType.default_value

    def get_default_value(self):
        etype = self._eType
        if etype is None:
            self.eType = ENativeType
            return object()
        default_literal = self.defaultValueLiteral
        if default_literal is not None:
            return etype.from_string(default_literal)
        if self.default_value is not None:
            return self.default_value
        return etype.default_value

    @property
    def is_reference(self):
        return False

    @property
    def is_attribute(self):
        return True


class EReference(EStructuralFeature):
    def __init__(self, name=None, eType=None, containment=False,
                 eOpposite=None, **kwargs):
        super().__init__(name, eType, **kwargs)
        self.containment = containment
        self.eOpposite = eOpposite
        if not isinstance(eType, EClass) and hasattr(eType, 'eClass'):
            self.eType = eType.eClass

    @staticmethod
    def get_default_value():
        return None

    @property
    def eOpposite(self):
        return self._eopposite

    @eOpposite.setter
    def eOpposite(self, value):
        self._eopposite = value
        if value:
            value._eopposite = self

    @property
    def container(self):
        return self._eopposite and self._eopposite.containment

    @property
    def is_reference(self):
        return True

    @property
    def is_attribute(self):
        return False


class EClass(EClassifier):
    def __new__(cls, name=None, superclass=None, metainstance=None, **kwargs):
        if not isinstance(name, str):
            raise BadValueError(got=name, expected=str)
        instance = super().__new__(cls)
        if isinstance(superclass, tuple):
            instance.eSuperTypes.extend(superclass)
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
            super_types = instance.__compute_supertypes()
            try:
                instance.python_class = type(name, super_types, attr_dict)
            except Exception:
                super_types = sorted(super_types,
                                     key=lambda x: len(x.eClass
                                                        .eAllSuperTypes()),
                                     reverse=True)
                instance.python_class = type(name,
                                             tuple(super_types),
                                             attr_dict)

        instance.__name__ = name
        return instance

    def __mro_entries__(self, old_base):
        return (self.python_class, )

    def __init__(self, name=None, superclass=None, abstract=False,
                 metainstance=None, **kwargs):
        super().__init__(name, **kwargs)
        self.abstract = abstract
        self._eternal_listener.append(self)

    def __call__(self, *args, **kwargs):
        if self.abstract:
            raise TypeError(f"Can't instantiate abstract EClass {self.name}")
        return self.python_class(*args, **kwargs)

    def allInstances(self=None, resources=None):
        if self is None:
            self = EClass
        if resources:
            yield from (x for x in self._instances
                        if isinstance(x, self) and x.eResource in resources)
        else:
            yield from (x for x in self._instances if isinstance(x, self))

    def notifyChanged(self, notif):
        # We do not update in case of static metamodel (could be changed)
        if getattr(self.python_class, '_staticEClass', False):
            return
        if notif.feature is EClass.eSuperTypes:
            new_supers = self.__compute_supertypes()
            try:
                self.python_class.__bases__ = new_supers
            except TypeError:
                new_supers = sorted(new_supers,
                                    key=lambda x: len(x.eClass
                                                       .eAllSuperTypes()),
                                    reverse=True)
                self.python_class.__bases__ = tuple(new_supers)
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
        # code = compile(eoperation.to_code(), "<str>", "exec")
        # exec(code, namespace)
        code = compile_restricted(eoperation.to_code(), '<inline>', 'exec')
        exec(code, safe_builtins, namespace)
        setattr(self.python_class, name, namespace[name])

    def __compute_supertypes(self):
        if not self.eSuperTypes:
            return (EObject,)
        else:
            eSuperTypes = list(self.eSuperTypes)
            if len(eSuperTypes) > 1 and EObject.eClass in eSuperTypes:
                eSuperTypes.remove(EObject.eClass)
            return tuple(x.python_class for x in eSuperTypes)

    def __repr__(self):
        return f'<{self.__class__.__name__} name="{self.name}">'

    @property
    def eAttributes(self):
        return [x for x in self.eStructuralFeatures
                if x.is_attribute]

    @property
    def eReferences(self):
        return [x for x in self.eStructuralFeatures
                if x.is_reference]

    def findEStructuralFeature(self, name):
        return next((f for f in self._eAllStructuralFeatures_gen()
                     if f.name == name),
                    None)

    def _eAllSuperTypes_gen(self):
        super_types = self.eSuperTypes
        yield from self.eSuperTypes
        for x in super_types:
            yield from x._eAllSuperTypes_gen()

    def eAllSuperTypes(self):
        return OrderedSet(self._eAllSuperTypes_gen())

    def _eAllStructuralFeatures_gen(self):
        yield from self.eStructuralFeatures
        for parent in self.eSuperTypes:
            yield from parent._eAllStructuralFeatures_gen()

    def eAllStructuralFeatures(self):
        return OrderedSet(self._eAllStructuralFeatures_gen())

    def eAllReferences(self):
        return set((x for x in self._eAllStructuralFeatures_gen()
                    if x.is_reference))

    def eAllAttributes(self):
        return set((x for x in self._eAllStructuralFeatures_gen()
                    if x.is_attribute))

    def _eAllOperations_gen(self):
        yield from self.eOperations
        for parent in self.eSuperTypes:
            yield from parent._eAllOperations_gen()

    def eAllOperations(self):
        return OrderedSet(self._eAllOperations_gen())

    def findEOperation(self, name):
        return next((f for f in self._eAllOperations_gen() if f.name == name),
                    None)

    def __instancecheck__(self, instance):
        return isinstance(instance, self.python_class)

    def __subclasscheck__(self, cls):
        return issubclass(cls, self.python_class)


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
        [orig_vars.pop(x) for x in slots]
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
        decoded = resource.resolve_object(self._proxy_path)
        if not hasattr(decoded, '_inverse_rels'):
            self._wrapped = decoded.eClass
        else:
            self._wrapped = decoded
        self._wrapped._inverse_rels.update(self._inverse_rels)
        self._inverse_rels = self._wrapped._inverse_rels
        self.resolved = True

    def delete(self, recursive=True):
        if recursive and self.resolved:
            [obj.delete() for obj in self.eAllContents()]
            # for obj in self.eAllContents():
            #     obj.delete()

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
            decoded = resource.resolve_object(self._proxy_path)
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
            decoded = resource.resolve_object(self._proxy_path)
            if not hasattr(decoded, '_inverse_rels'):
                self._wrapped = decoded.eClass
            else:
                self._wrapped = decoded
            self.resolved = True
        self._wrapped.__setattr__(name, value)

    def __instancecheck__(self, instance):
        self.force_resolve()
        return self._wrapped.__instancecheck__(instance)

    def __call__(self, *args, **kwargs):
        self.force_resolve()
        return self._wrapped(*args, **kwargs)

    def __hash__(self):
        return object.__hash__(self)

    def __eq__(self, other):
        self.force_resolve()
        return self._wrapped == other

    def __ne__(self, other):
        self.force_resolve()
        return self._wrapped != other


def abstract(cls):
    cls.eClass.abstract = True
    return cls


from .valuecontainer import ECollection, EValue, \
                            EList, EOrderedSet, ESet, EBag, \
                            EDerivedCollection, \
                            EcoreUtils, \
                            BadValueError  # noqa


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
EInteger = EDataType('EInteger', int, 0, from_string=int)
EInt = EDataType('EInt', int, 0, from_string=int)
ELong = EDataType('ELong', int, 0, from_string=int)
ELongObject = EDataType('ELongObject', int, from_string=int)
EIntegerObject = EDataType('EIntegerObject', int, from_string=int)
EBigInteger = EDataType('EBigInteger', int, from_string=int)
EDouble = EDataType('EDouble', float, 0.0, from_string=float)
EDoubleObject = EDataType('EDoubleObject', float, from_string=float)
EFloat = EDataType('EFloat', float, 0.0, from_string=float)
EFloatObject = EDataType('EFloatObject', float, from_string=float)
EStringToStringMapEntry = EDataType('EStringToStringMapEntry', dict,
                                    type_as_factory=True)
EFeatureMapEntry = EDataType('EFeatureMapEntry', dict, type_as_factory=True)
EDiagnosticChain = EDataType('EDiagnosticChain', str)
ENativeType = EDataType('ENativeType', object)
EJavaObject = EDataType('EJavaObject', object)
EDate = EDataType('EDate', datetime,
                  from_string=parse_date,
                  to_string=lambda d: d.strftime('%Y-%m-%dT%H:%M:%S.%f%z'))
EBigDecimal = EDataType('EBigDecimal', Decimal, from_string=Decimal)
EByte = EDataType('EByte', bytes)
EByteObject = EDataType('EByteObject', bytes)
EByteArray = EDataType('EByteArray', bytearray)
EChar = EDataType('EChar', str)
ECharacterObject = EDataType('ECharacterObject', str)
EShort = EDataType('EShort', int, from_string=int)
EShortObject = EDataType('EShortObject', int, from_string=int)
EJavaClass = EDataType('EJavaClass', type)


EModelElement.eAnnotations = EReference('eAnnotations', EAnnotation,
                                        upper=-1, containment=True)
EAnnotation.eModelElement = EReference('eModelElement', EModelElement,
                                       eOpposite=EModelElement.eAnnotations)
EAnnotation.source = EAttribute('source', EString)
EAnnotation.details = EAttribute('details', EStringToStringMapEntry)
EAnnotation.references = EReference('references', EObject, upper=-1)
EAnnotation.contents = EReference('contents', EObject, upper=-1,
                                  containment=True)

ETypedElement.ordered = EAttribute('ordered', EBoolean, default_value=True)
ETypedElement.unique = EAttribute('unique', EBoolean, default_value=True)
ETypedElement._lower = EAttribute('lower', EInteger, derived=True)
ETypedElement.lowerBound = EAttribute('lowerBound', EInteger)
ETypedElement._upper = EAttribute('upper', EInteger, derived=True)
ETypedElement.upperBound = EAttribute('upperBound', EInteger, default_value=1)
ETypedElement.required = EAttribute('required', EBoolean)
ETypedElement.eGenericType = EReference('eGenericType', EGenericType,
                                        containment=True)
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
EClassifier.instanceTypeName = EAttribute('instanceTypeName', EString)
EClassifier.instanceClass = EAttribute('instanceClass', EJavaClass)
EClassifier.defaultValue = EAttribute('defaultValue', EJavaObject)
EClassifier.instanceTypeName = EAttribute('instanceTypeName', EString,
                                          volatile=True, unsettable=True)

EDataType.instanceClassName_ = EAttribute('instanceClassName', EString)
EDataType.serializable = EAttribute('serializable', EBoolean)

EClass.abstract = EAttribute('abstract', EBoolean)
EClass.eStructuralFeatures = EReference('eStructuralFeatures',
                                        EStructuralFeature,
                                        upper=-1, containment=True)
EClass.eGenericSuperTypes = EReference('eGenericSuperTypes', EGenericType,
                                       containment=True, upper=-1)
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
EOperation.eGenericExceptions = EReference('eGenericExceptions', EGenericType,
                                           upper=-1)

EParameter.eOperation = EReference('eOperation', EOperation,
                                   eOpposite=EOperation.eParameters)

ETypeParameter.eBounds = EReference('eBounds', EGenericType,
                                    upper=-1, containment=True)
ETypeParameter.eGenericType = EReference('eGenericType', EGenericType,
                                         upper=-1)
EGenericType.eClassifier = EReference('eClassifier', EClassifier)
EGenericType.eTypeArguments = EReference('eTypeArguments', EGenericType,
                                         containment=True, upper=-1)
EGenericType.eTypeParameter = EReference('eTypeParameter', ETypeParameter,
                                         eOpposite=ETypeParameter.eGenericType)
EGenericType.eUpperBound = EReference('eUpperBound', EGenericType)
EGenericType.eLowerBound = EReference('eLowerBound', EGenericType)

register_classifier = Core.register_classifier


def register_metaclass(c, metaclass=MetaEClass, *args, **kwargs):
    register_classifier(c, *args, **kwargs)
    c.__class__ = metaclass


eClass = EPackage(name=name, nsURI=nsURI, nsPrefix=nsPrefix)
register_metaclass(EObject, promote=True, abstract=True,
                   metaclass=Metasubinstance)
register_metaclass(EModelElement, promote=True, abstract=True)
register_metaclass(ENamedElement, promote=True, abstract=True)
register_metaclass(EAnnotation, promote=True)
register_metaclass(EPackage, promote=True, metaclass=SpecialEPackage)
register_metaclass(EGenericType, promote=True)
register_metaclass(ETypeParameter, promote=True)
register_metaclass(ETypedElement, promote=True)
register_metaclass(EClassifier, promote=True, abstract=True)
register_metaclass(EDataType, promote=True)
register_metaclass(EEnum, promote=True)
register_metaclass(EEnumLiteral, promote=True)
register_metaclass(EParameter, promote=True)
register_metaclass(EOperation, promote=True)
register_metaclass(EStructuralFeature, promote=True, abstract=True)
register_metaclass(EAttribute, promote=True)
register_metaclass(EReference, promote=True)
register_metaclass(EClass, promote=True)
register_classifier(EString)
register_classifier(EBoolean)
register_classifier(EInteger)
register_classifier(EInt)
register_classifier(EBigInteger)
register_classifier(EIntegerObject)
register_classifier(EFloat)
register_classifier(EFloatObject)
register_classifier(EDouble)
register_classifier(EDoubleObject)
register_classifier(EStringToStringMapEntry)
register_classifier(EFeatureMapEntry)
register_classifier(EDiagnosticChain)
register_classifier(ENativeType)
register_classifier(EJavaObject)
register_classifier(EDate)
register_classifier(EBigDecimal)
register_classifier(EBooleanObject)
register_classifier(ELongObject)
register_classifier(ELong)
register_classifier(EByte)
register_classifier(EByteObject)
register_classifier(EByteArray)
register_classifier(EChar)
register_classifier(ECharacterObject)
register_classifier(EShort)
register_classifier(EShortObject)
register_classifier(EJavaClass)
eContents = eClass.eContents


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
           'EShort', 'EShortObject', 'EJavaClass', 'EMetaclass',
           'EDerivedCollection']
