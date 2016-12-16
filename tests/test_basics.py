import pytest
from pyecore.ecore import *

def test_ecore_URI():
    assert nsURI == 'http://www.eclipse.org/emf/2002/Ecore'


def test_get_existing_EClassifier():
    assert getEClassifier('EClass')


def test_get_nonexisting_EClassifier():
    assert not getEClassifier('EEClass')


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
    print(MyEnum)
