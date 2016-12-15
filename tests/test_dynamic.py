import pytest
from pyecore.ecore import *


def test_create_dynamic_eclass():
    A = EClass('A')
    assert isinstance(A, EObject) and isinstance(A, EClass)


def test_create_dynamic_instance():
    A = EClass('A')
    instance = A()
    assert EcoreUtils.isinstance(instance, A)
    assert isinstance(instance, EObject)


def test_create_dynamic_simple_ereference():
    A = EClass('A')
    B = EClass('B')
    A.eReferences.append(EReference('tob', B))
    a1 = A()
    b1 = B()
    a1.tob = b1
    assert a1.tob is b1


def test_create_dynamic_simple_ereference_wrongtype():
    A = EClass('A')
    B = EClass('B')
    A.eReferences.append(EReference('tob', B))
    a1 = A()
    with pytest.raises(BadValueError):
        a1.tob = 3


def test_create_dynamic_simple_ereference_unset():
    A = EClass('A')
    B = EClass('B')
    A.eReferences.append(EReference('tob', B))
    a1 = A()
    b1 = B()
    a1.tob = b1
    a1.tob = None
    assert a1.tob is None


def test_create_dynamic_many_ereference():
    A = EClass('A')
    B = EClass('B')
    A.eReferences.append(EReference('tob', B, upper=-1))
    a1 = A()
    b1 = B()
    a1.tob.append(b1)
    assert a1.tob and b1 in a1.tob and len(a1.tob) == 1


def test_create_dynamic_many_ereference_wrongtype():
    A = EClass('A')
    B = EClass('B')
    A.eReferences.append(EReference('tob', B, upper=-1))
    a1 = A()
    with pytest.raises(BadValueError):
        a1.tob.append(3)


def test_create_dynamic_many_ereference_remove():
    A = EClass('A')
    B = EClass('B')
    A.eReferences.append(EReference('tob', B, upper=-1))
    a1 = A()
    b1 = B()
    a1.tob.append(b1)
    a1.tob.remove(b1)
    assert a1.tob == []


def test_create_dynamic_ereference_one2one():
    A = EClass('A')
    B = EClass('B')
    A.eReferences.append(EReference('b', B))
    B.eReferences.append(EReference('a', A, eOpposite=A.eReferences[0]))
    a1 = A()
    b1 = B()
    a1.b = b1
    assert a1.b is b1
    assert b1.a is a1


def test_create_dynamic_ereference_one2one_unset():
    A = EClass('A')
    B = EClass('B')
    A.eReferences.append(EReference('b', B))
    B.eReferences.append(EReference('a', A, eOpposite=A.eReferences[0]))
    a1 = A()
    b1 = B()
    a1.b = b1
    assert a1.b is b1
    assert b1.a is a1
    a1.b = None
    assert a1.b is None
    assert b1.a is None


def test_create_dynamic_ereference_many2one():
    A = EClass('A')
    B = EClass('B')
    A.eReferences.append(EReference('b', B, upper=-1))
    B.eReferences.append(EReference('a', A, eOpposite=A.eReferences[0]))
    a1 = A()
    b1 = B()
    a1.b.append(b1)
    assert b1 in a1.b and len(a1.b) == 1
    assert b1.a is a1


def test_create_dynamic_ereference_many2one_unset():
    A = EClass('A')
    B = EClass('B')
    A.eReferences.append(EReference('b', B, upper=-1))
    B.eReferences.append(EReference('a', A, eOpposite=A.eReferences[0]))
    a1 = A()
    b1 = B()
    a1.b.append(b1)
    assert b1 in a1.b and len(a1.b) == 1
    assert b1.a is a1
    a1.b.remove(b1)
    assert b1 not in a1.b and a1.b == []
    assert b1.a is None


def test_create_dynamic_ereference_one2many():
    A = EClass('A')
    B = EClass('B')
    A.eReferences.append(EReference('b', B))
    B.eReferences.append(EReference('a', A, upper=-1, eOpposite=A.eReferences[0]))
    a1 = A()
    b1 = B()
    a1.b = b1
    assert a1.b is b1
    assert a1 in b1.a and len(b1.a) == 1


def test_create_dynamic_ereference_one2many_unset():
    A = EClass('A')
    B = EClass('B')
    A.eReferences.append(EReference('b', B))
    B.eReferences.append(EReference('a', A, upper=-1, eOpposite=A.eReferences[0]))
    a1 = A()
    b1 = B()
    a1.b = b1
    assert a1.b is b1
    assert a1 in b1.a and len(b1.a) == 1
    a1.b = None
    assert a1 not in b1.a and b1.a == []
    assert a1.b is None


def test_create_dynamic_ereference_many2many():
    A = EClass('A')
    B = EClass('B')
    A.eReferences.append(EReference('b', B, upper=-1))
    B.eReferences.append(EReference('a', A, upper=-1, eOpposite=A.eReferences[0]))
    a1 = A()
    b1 = B()
    a1.b.append(b1)
    assert b1 in a1.b and len(a1.b) == 1
    assert a1 in b1.a and len(b1.a) == 1


def test_create_dynamic_ereference_many2many_unset():
    A = EClass('A')
    B = EClass('B')
    A.eReferences.append(EReference('b', B, upper=-1))
    B.eReferences.append(EReference('a', A, upper=-1, eOpposite=A.eReferences[0]))
    a1 = A()
    b1 = B()
    a1.b.append(b1)
    assert b1 in a1.b
    assert a1 in b1.a
    a1.b.remove(b1)
    assert b1 not in a1.b and a1.b == []
    assert a1 not in b1.a and b1.a == []


def test_create_dynamic_inheritances():
    A = EClass('A')
    B = EClass('B', superclass=A)
    b1 = B()
    assert EcoreUtils.isinstance(b1, B)
    assert EcoreUtils.isinstance(b1, A)


def test_create_dynamic_multi_inheritances():
    A = EClass('A')
    B = EClass('B')
    C = EClass('C', superclass=(A, B))
    c1 = C()
    assert EcoreUtils.isinstance(c1, C)
    assert EcoreUtils.isinstance(c1, B)
    assert EcoreUtils.isinstance(c1, A)


def test_create_dynamic_abstract_eclass():
    A = EClass('A', abstract=True)
    with pytest.raises(TypeError):
        A()


def test_create_dynamic_subclass_from_abstract_eclass():
    A = EClass('A', abstract=True)
    B = EClass('B', superclass=A)
    b = B()
    assert EcoreUtils.isinstance(b, B)
    assert EcoreUtils.isinstance(b, A)
