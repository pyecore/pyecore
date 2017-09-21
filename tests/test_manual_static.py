import pytest
from pyecore.ecore import *


String = EDataType('String', eType=str, default_value='default_name')
Integer = EDataType('Integer', eType=int, default_value=0)


class A(EObject, metaclass=MetaEClass):
    name = EAttribute(eType=String)
    age = EAttribute(eType=Integer)
    to_b = EReference()

    def __init__(self, name=None):
        super().__init__()
        if name:
            self.name = name


class B(EObject, metaclass=MetaEClass):
    to_a = EReference(eType=A, eOpposite=A.to_b)

    def __init__(self):
        super().__init__()


A.to_b.eType = B


def test_static_metamodel_simple_instance():
    a = A()
    assert a.name == 'default_name'
    assert a.age == 0

    a = A('John')
    assert a.name == 'John'

    a.age = 15
    assert a.age == 15


def test_static_metamodel_link_instance():
    a = A()
    b = B()
    assert a.to_b is None
    assert b.to_a is None

    a.to_b = b
    assert a.to_b is b
    assert b.to_a is a


def test_static_metamodel_reorder_mro():
    class A(EObject, metaclass=MetaEClass):
        name = EAttribute(eType=EString)

        def __init__(self):
            super().__init__()

    A._staticEClass = False  # Enable static EClass auto-update

    B = EClass('B')

    a = A()
    assert not isinstance(a, B.python_class)

    A.eClass.eSuperTypes.append(B)
    assert isinstance(a, B.python_class)
