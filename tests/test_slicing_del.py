import pytest
from pyecore.ecore import *
from pyecore.utils import DynamicEPackage
from pyecore.notification import *


@pytest.fixture(scope='module')
def simplemm():
    A = EClass('A')
    B = EClass('B')
    A.eStructuralFeatures.append(EAttribute('name', EString))
    A.eStructuralFeatures.append(EAttribute('number', EInt))
    A.eStructuralFeatures.append(EReference('b', B))
    A.eStructuralFeatures.append(EAttribute('names', EString, upper=-1, unique=False))
    A.eStructuralFeatures.append(EAttribute('ints', EInt, upper=-1, unique=False))
    A.eStructuralFeatures.append(EReference('inners', B, upper=-1, unique=False, containment=True))
    A.eStructuralFeatures.append(EReference('cols', B, upper=-1, unique=False))
    pack = EPackage('pack', nsURI='http://pack/1.0', nsPrefix='pack')
    pack.eClassifiers.extend([A, B])
    return DynamicEPackage(pack)


class ObserverCounter(EObserver):
    def __init__(self, notifier=None):
        super(ObserverCounter, self).__init__(notifier=notifier)
        self.calls = 0

    def notifyChanged(self, notification):
        self.calls += 1
        self.kind = notification.kind
        self.feature = notification.feature


def test_slicing_int_list(simplemm):
    a = simplemm.A()
    a.ints.extend([1, 2, 3, 4])
    a.ints[0:0] = [0]
    assert a.ints == [0, 1, 2, 3, 4]

    a.ints[0:2] = [0]
    assert a.ints == [0, 2, 3, 4]

    a.ints[0:1] = [1, 10]
    assert a.ints == [1, 10, 2, 3, 4]

    a.ints[1:] = [5]
    assert a.ints == [1, 5]

    a.ints[:] = [3, 2, 1]
    assert a.ints == [3, 2, 1]


def test_slicing_str_list(simplemm):
    a = simplemm.A()
    a.names.extend(['a', 'b', 'c', 'd'])
    a.names[0:0] = ['z']
    assert a.names == ['z', 'a', 'b', 'c', 'd']

    a.names[0:2] = ['za']
    assert a.names == ['za', 'b', 'c', 'd']

    a.names[0:1] = ['z', 'a']
    assert a.names == ['z', 'a', 'b', 'c', 'd']

    a.names[1:] = ['f']
    assert a.names == ['z', 'f']

    a.names[:] = ['r', 't', 'y']
    assert a.names == ['r', 't', 'y']


def test_slicing_obj_noncontainment_list(simplemm):
    a = simplemm.A()
    b1 = simplemm.B()
    b2 = b1.eClass()
    b3 = b1.eClass()
    a.cols.extend([b1, b2, b3])

    b4 = b1.eClass()
    a.cols[0:0] = [b4]
    assert a.cols == [b4, b1, b2, b3]

    a.cols[0:2] = [b3]
    assert a.cols == [b3, b2, b3]

    a.cols[0:1] = [b1, b4]
    assert a.cols == [b1, b4, b2, b3]

    b5 = b1.eClass()
    a.cols[1:] = [b5]
    assert a.cols == [b1, b5]

    a.cols[:] = [b4, b3, b2]
    assert a.cols == [b4, b3, b2]


def test_slicing_obj_containment_list(simplemm):
    a = simplemm.A()
    b1 = simplemm.B()
    a.inners.append(b1)
    assert b1.eContainer() is a

    b2 = b1.eClass()
    a.inners[0:1] = [b2]
    assert b2 in a.inners
    assert b2.eContainer() is a
    assert b1.eContainer() is None

    b3 = b1.eClass()
    b4 = b1.eClass()
    a.inners.extend([b3, b4])
    assert b3.eContainer() is a and b4.eContainer() is a
    b5 = b1.eClass()
    a.inners[1:] = [b5]
    assert b3.eContainer() is None and b4.eContainer() is None
    assert b5.eContainer() is a
    assert b5 in a.inners


def test_slicing_int_list_bad_obj(simplemm):
    a = simplemm.A()
    a.ints.extend([1, 2, 3, 4])
    with pytest.raises(BadValueError):
        a.ints[1:] = ['r']


def test_slicing_obj_list_bad_obj(simplemm):
    a = simplemm.A()
    with pytest.raises(BadValueError):
        a.cols[:] = [simplemm.A()]


def test_slicing_insert_ints(simplemm):
    a = simplemm.A()
    a.ints.insert(0, 1)
    assert a.ints == [1]


def test_slicing_pop_b(simplemm):
    a = simplemm.A()
    b1 = simplemm.B()
    b2 = simplemm.B()
    a.cols.extend([b1, b2])
    o = ObserverCounter(a)
    e = a.cols.pop(1)
    assert e is b2
    assert o.calls == 1
    assert o.kind == Kind.REMOVE

    e = a.cols.pop()
    assert o.calls == 2
    assert o.kind == Kind.REMOVE


def test_del_single_attribute(simplemm):
    a = simplemm.A()
    default_value = a.name
    a.name = 'test_name'
    assert a.name == 'test_name' and a.name != default_value

    del a.name
    assert a.name is None

    default_value = a.number
    a.number = 4
    assert a.number == 4 and a.number != default_value
    del a.number
    assert a.number == default_value


def test_del_single_reference(simplemm):
    a = simplemm.A()
    default_value = a.b
    b = simplemm.B()
    a.b = b
    assert a.b is b and a.b is not default_value
    del a.b
    assert a.b is default_value


def test_del_multiple_attribute(simplemm):
    a = simplemm.A()
    default_value = list(a.ints)
    a.ints.append(4)
    assert a.ints == [4] and a.ints != default_value

    del a.ints
    assert a.ints == default_value


def test_del_multiple_reference(simplemm):
    a = simplemm.A()
    default_value = list(a.inners)
    b1 = simplemm.B()
    b2 = simplemm.B()
    a.inners.extend([b1, b2])
    assert a.inners == [b1, b2] and a.inners != default_value

    del a.inners
    assert a.inners == default_value
