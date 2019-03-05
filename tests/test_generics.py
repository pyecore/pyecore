import pytest
from pyecore.ecore import *


def test_simple_generics():
    @EMetaclass
    class A(object):
        T = ETypeParameter(eBounds=(EGenericType(eClassifier=EString),
                                    EGenericType(eClassifier=EInt)))
        mylist = EAttribute(eGenericType=EGenericType(T), upper=-1)
        toa = EReference(eGenericType=EGenericType(T))
        tonothing = EReference()

    assert str(A.T)

    a = A()
    a.mylist.append('abc')
    a.mylist.append(45)

    assert 45 in a.mylist
    assert 'abc' in a.mylist

    with pytest.raises(Exception):
        a.toa = b

    b = A()
    A.T.eBounds.clear()
    a.toa = b
    assert a.toa is b

    with pytest.raises(AttributeError):
        a.tonothing = 4
