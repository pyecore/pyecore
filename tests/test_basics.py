import pytest
from pyecore.ecore import *
import pyecore.ecore as Ecore


def test_ecore_URI():
    assert Ecore.nsURI == 'http://www.eclipse.org/emf/2002/Ecore'


def test_get_existing_EClassifier():
    assert Ecore.getEClassifier('EClass')


def test_get_nonexisting_EClassifier():
    assert not Ecore.getEClassifier('EEClass')


def test_ecoreutil_isinstance_none():
    assert EcoreUtils.isinstance(None, EClass)


def test_ecoreutil_isinstance_integer():
    assert EcoreUtils.isinstance(100, EInteger)


def test_ecoreutil_isinstance_string():
    assert EcoreUtils.isinstance('test', EString)


def test_ecoreutil_isinstance_boolean():
    assert EcoreUtils.isinstance(True, EBoolean)


def test_ecoreutil_isinstance_estringtostringmap():
    assert EcoreUtils.isinstance({3: '3'}, EStringToStringMapEntry)


def test_eenum_empty_instance():
    MyEnum = EEnum('MyEnum')
    assert not MyEnum.default_value
    assert not MyEnum.eLiterals


def test_eenum_simple_instance():
    MyEnum = EEnum('MyEnum', literals=['A', 'B', 'C'])
    assert MyEnum.default_value
    assert MyEnum.default_value is MyEnum.A


def test_eenum_simple_instance_with_defaultvalue():
    MyEnum = EEnum('MyEnum', literals=['A', 'B', 'C'], default_value='B')
    assert MyEnum.default_value
    assert MyEnum.default_value is MyEnum.B


def test_eenum_simple_instance_with_defaultvalue():
    with pytest.raises(AttributeError):
        MyEnum = EEnum('MyEnum', literals=['A', 'B', 'C'], default_value='D')


def test_eenum_simple_instance():
    MyEnum = EEnum('MyEnum', literals=['A', 'B', 'C'])
    assert EcoreUtils.isinstance(MyEnum.A, EEnumLiteral)


def test_eenum_simple_search():
    MyEnum = EEnum('MyEnum', literals=['A', 'B', 'C'])
    assert MyEnum.A in MyEnum
    assert 'A' in MyEnum


def test_eenum_geteenum():
    MyEnum = EEnum('MyEnum', literals=['A', 'B', 'C'])
    assert MyEnum.getEEnumLiteral(name='A') is MyEnum.A
    assert MyEnum.getEEnumLiteral(value=1) is MyEnum.B
    assert MyEnum.getEEnumLiteral('F') is None


def test_eenum_geteenum_print():
    MyEnum = EEnum('MyEnum', literals=['A', 'B', 'C'])
    assert MyEnum.__repr__()


def test_eenumliteral_geteenum_str():
    MyEnum = EEnum('MyEnum', literals=['A', 'B', 'C'])
    assert str(MyEnum.A) == 'A'
    assert str(MyEnum.B) == 'B'
    assert str(MyEnum.C) == 'C'


def test_eattribute_etype():
    eattribute = EAttribute('test')
    assert ETypedElement.eClass in eattribute.eClass.eAllSuperTypes()
    assert eattribute.eClass.findEStructuralFeature('eType')


def test_eobject_egetset_badtype():
    eattribute = EAttribute('eatt')
    with pytest.raises(TypeError):
        eattribute.eGet(4)
    with pytest.raises(TypeError):
        eattribute.eSet(4, 4)


def test_eobject_eget_simple():
    eattribute = EAttribute('eatt')
    assert eattribute.eGet('name') == 'eatt'
    name = eattribute.eClass.findEStructuralFeature('name')
    assert eattribute.eGet(name) == 'eatt'


def test_eobject_eget_many():
    A = EClass('A')
    assert A.eGet('eAttributes') == []
    eattributes = A.eClass.findEStructuralFeature('eAttributes')
    assert A.eGet(eattributes) == []
    a_name = EAttribute('a_name')
    A.eGet('eStructuralFeatures').append(a_name)
    assert A.eGet('eStructuralFeatures') != [] and A.eGet('eStructuralFeatures')[0] is a_name


def test_eobject_eset_simple():
    eattribute = EAttribute()
    assert eattribute.name is None
    eattribute.eSet('name', 'test')
    assert eattribute.name == 'test'
    name = eattribute.eClass.findEStructuralFeature('name')
    eattribute.eSet(name, 'test2')
    assert eattribute.name == 'test2'


def test_estructuralfeature_repr():
    eattribute = EAttribute()
    assert eattribute.__repr__() is not None


def test_urifragment_default():
    assert Ecore.default_eURIFragment() == '/'


def test_urifragment_ecore():
    assert Ecore.eURIFragment() == '#/'


def test_urifragment_static_ecore():
    assert EClass.eClass.eURIFragment() == '#//EClass'
    assert EPackage.eClass.eURIFragment() == '#//EPackage'
    assert EDataType.eClass.eURIFragment() == '#//EDataType'


def test_modelelement_annotation():
    annotation1 = EAnnotation('SOURCE1')
    annotation2 = EAnnotation('SOURCE2')

    m = EModelElement()
    m.eAnnotations.extend((annotation1, annotation2))

    assert not m.getEAnnotation(None)
    assert m.getEAnnotation('SOURCE1') is annotation1
    assert m.getEAnnotation('SOURCE2') is annotation2
    assert not m.getEAnnotation('SOURCE3')


def test_typedelement_lower_upper():
    ref = EAttribute('names', EString, upper=-1, lower=1)
    assert ref.upper == -1
    assert ref.lower == 1

    ref.upperBound = 1
    ref.lowerBound = 0
    assert ref.upper == 1
    assert ref.lower == 0


def test_subclass():
    @EMetaclass
    class A(object):
        pass

    class B(A):
        pass

    assert issubclass(B, A)

    C = EClass('C', superclass=(A.eClass,))
    assert issubclass(C, A)

    D = EClass('D', superclass=(C,))
    assert issubclass(D, C)

    class E(D.python_class):
        pass

    assert issubclass(E, C)
    with pytest.raises(Exception):
        c = C()
        assert issubclass(c, A)


def test_container():
    A = EClass('A')
    A.eStructuralFeatures.append(EReference('first', A, containment=True))
    A.eStructuralFeatures.append(EReference('second', A, containment=True,
                                            upper=-1))
    root, a1 = A(), A()
    root.first = a1

    assert root.first is a1
    assert a1 not in root.second

    root.second.append(a1)
    assert root.first is None
    assert a1 in root.second

    root.first = a1
    assert root.first is a1
    assert a1 not in root.second


def test_collection_comprehension():
    A = EClass('A')
    A.eStructuralFeatures.append(EReference('toa', A, upper=-1, derived=True))
    A.eStructuralFeatures.append(EAttribute('stuffs', EString, upper=-1,
                                            derived=True))

    root = A()
    assert isinstance(root.toa, EDerivedCollection)

    with pytest.raises(Exception):
        root.toa.append(A())

    assert isinstance(root.stuffs, EDerivedCollection)
    with pytest.raises(Exception):
        root.stuffs.append('test')


def test_collection_affectation():
    A = EClass('A')
    A.eStructuralFeatures.append(EReference('toa', A, upper=-1))
    A.eStructuralFeatures.append(EAttribute('name', EString))

    x, y = A(), A()

    a = A(name='tes')
    with pytest.raises(BadValueError):
        x.toa = [a]

    x.toa.append(a)

    with pytest.raises(AttributeError):
        y.toa = x.toa

    b = A()
    y.toa += [b]
    assert b in y.toa
    assert b not in x.toa


def test_many_references_non_0_or_minu1():
    @EMetaclass
    class Wheel(object):
        pass

    @EMetaclass
    class Car(object):
        names = EAttribute(eType=EString, upper=4, lower=4)
        wheels = EReference(eType=Wheel, upper=2, lower=2)

    c = Car()
    assert len(c.wheels) == 0
    assert len(c.names) == 0


def test_allinstances_static():
    @EMetaclass
    class A(object):
        pass

    a = A()
    b = A()
    assert a in A.allInstances()
    assert b in A.allInstances()

    from pyecore.resources import ResourceSet
    rset = ResourceSet()
    r1 = rset.create_resource('http://test1')
    r2 = rset.create_resource('http://test2')

    r1.append(a)
    r2.append(b)
    assert a in A.allInstances(resources=(r1,))
    assert a not in A.allInstances(resources=(r2,))
    assert b in A.allInstances(resources=(r2,))
    assert b not in A.allInstances(resources=(r1,))


def test_allinstances_dynamic():
    A = EClass('A')

    a = A()
    b = A()
    assert a in A.allInstances()
    assert b in A.allInstances()

    from pyecore.resources import ResourceSet
    rset = ResourceSet()
    r1 = rset.create_resource('http://test1')
    r2 = rset.create_resource('http://test2')

    r1.append(a)
    r2.append(b)
    assert a in A.allInstances(resources=(r1,))
    assert a not in A.allInstances(resources=(r2,))
    assert b in A.allInstances(resources=(r2,))
    assert b not in A.allInstances(resources=(r1,))


def test_allinstances_ecore():
    assert EClass.eClass in EClass.allInstances()

    A = EClass('A')

    @EMetaclass
    class B(object):
        pass

    assert A in EClass.allInstances()
    assert B.eClass in EClass.allInstances()

    assert EClass.eClass in EClassifier.allInstances()
    assert EInt in EDataType.allInstances()


def test_eobject_egetset_badtype_exception():
    A = EClass('A')
    name_attribute = EAttribute('name', EProxy(wrapped=EString))
    A.eStructuralFeatures.append(name_attribute)

    a = A()
    with pytest.raises(BadValueError) as e:
        a.name = 32

    e = e.value
    assert e.expected is EString
    assert e.got == 32
    assert e.feature is name_attribute



def test_eobject_eproxy_basicoperations():
    A = EClass('A')
    B = EClass('B')
    aProxy = EProxy(wrapped=A)
    bProxy = EProxy(wrapped=B)
    cProxy = EProxy(wrapped=A)

    assert aProxy == aProxy
    assert aProxy == cProxy
    assert aProxy != bProxy
    assert bProxy != cProxy
    assert hash(aProxy) != hash(A)

    a = aProxy()
    assert isinstance(a, aProxy)


def test_eattribute_defaultvalueliteral_dynamic():
    A = EClass('A')
    A.eStructuralFeatures.append(EAttribute('age', EInt,
                                            defaultValueLiteral='42'))
    a = A()
    assert a.age == 42
