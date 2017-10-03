import pytest
from pyecore.ecore import OrderedSet


def test_orderedset_insert_empty():
    o = OrderedSet()
    o.insert(0, 125)
    assert o == [125]

    o.clear()
    o.insert(12, 135)
    assert o == [135]

    o.clear()
    o.insert(-1, 145)
    assert o == [145]


def test_orderedset_insert_nonempty():
    o = OrderedSet([1, 2])
    o.insert(0, 125)
    assert o == [125, 1, 2]

    o = OrderedSet([1, 2])
    o.insert(12, 135)
    assert o == [1, 2, 135]

    o = OrderedSet([1, 2])
    o.insert(-1, 145)
    assert o == [1, 145, 2]

    o = OrderedSet([1, 2, 3])
    o.insert(-2, 145)
    assert o == [1, 145, 2, 3]


def test_orderedset_pop_empty():
    o = OrderedSet()
    with pytest.raises(KeyError):
        o.pop()


def test_orderedset_pop_nonempty():
    o = OrderedSet([1, 2, 3])
    o.pop()
    assert o == [1, 2]

    o = OrderedSet([1, 2, 3])
    o.pop(1)
    assert o == [1, 3]

    o = OrderedSet([1, 2, 3])
    o.pop(-1)
    assert o == [1, 2]

    o = OrderedSet([1, 2, 3])
    with pytest.raises(IndexError):
        o.pop(45)

    with pytest.raises(IndexError):
        o.pop(-45)

    assert o == [1, 2, 3]


def test_orderedset_setitem():
    o = OrderedSet([1, 2, 3])
    o[0] = 12
    assert o == [12, 2, 3]

    o[-1] = 14
    assert o == [12, 2, 14]

    o[-2] = 13
    assert o == [12, 13, 14]


def test_orderedset_setitem_outofrange():
    o = OrderedSet([1, 2, 3])
    with pytest.raises(IndexError):
        o[-5] = 5

    with pytest.raises(IndexError):
        o[5] = 5

    assert o == [1, 2, 3]


def test_orderedset_setitem_slice():
    o = OrderedSet([1, 2, 3])

    with pytest.raises(KeyError):
        o[:] = [4, 5]
