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
    class C(EObject, metaclass=MetaEClass):
        inner = EAttribute(eType=EString)

        def __init__(self):
            super().__init__()

    C._staticEClass = False  # Enable static EClass auto-update

    D = EClass('D')

    a = C()
    assert not isinstance(a, D.python_class)

    C.eClass.eSuperTypes.append(D)
    assert isinstance(a, D.python_class)


def test_static_metamodel_annotation():
    @EMetaclass
    class C1(object):
        a = EAttribute(eType=EString)
        b = EAttribute(eType=EInt)

    class C2(C1):
        __slots__ = 'd'
        c = EAttribute(eType=EInt)

        def __init__(self):
            self.d = 6

    c2 = C2()
    assert c2.a is None
    assert c2.b == 0
    assert c2.c == 0
    assert c2.d == 6


def test_static_metamodel_mixin():
    class Mixin(object):
        value = 5

    @EMetaclass
    class C3(Mixin):
        __slots__ = 'a'

        def __init__(self):
            self.a = 5

    c = C3()
    assert c.value == 5
    assert c.eClass.python_class is C3
    assert c.a == 5


def test_static_change_baseclasses():
    @EMetaclass
    class C4(EObject):
        pass

    A = EClass('A')
    C4.eClass.eSuperTypes.append(A)

    assert EObject.eClass not in C4.eClass.eSuperTypes


def test_static_eall_attributes_references():
    @EMetaclass
    class A(object):
        a = EAttribute(eType=EString)
        b = EAttribute(eType=EInt)

    @EMetaclass
    class B(A):
        c = EAttribute(eType=EString)
        a_ref = EReference(eType=A)

    @EMetaclass
    class C(B):
        d = EAttribute(eType=EBoolean)

    assert C.eClass.eAllAttributes() == {A.a, A.b, B.c, C.d}
    assert C.eClass.eAllReferences() == {B.a_ref}
