import pytest
from pyecore.ecore import *
from pyecore.behavior import behavior, main, run


def test_static_metamodel_behavior_injection():
    @EMetaclass
    class A(object):
        pass

    @A.behavior
    def my_fun(self):
        return True

    @A.behavior
    def __init__(self, i=15):
        self.i = i

    a = A()
    assert a.my_fun() is True
    assert a.i == 15

    a = A(i=0)
    assert a.i == 0


def test_static_metamodel_entry_point():
    @EMetaclass
    class A(object):
        pass

    @A.behavior
    def my_fun(self, i):
        return i + 1

    a = A()
    x = 1
    with pytest.raises(NotImplementedError):
        run(a)

    # We add the behavior *after* the instance creation
    @main
    @A.behavior
    def entry_point(self, i=0):
        return self.my_fun(i)

    y = run(a, x)
    assert y == x + 1


def test_dynamic_metamodel_behavior_injection():
    A = EClass('A')

    @A.behavior
    def my_fun(self):
        return True

    @A.behavior
    def __init__(self, i=15):
        self.i = i

    a = A()
    assert a.my_fun() is True
    assert a.i == 15

    a = A(i=0)
    assert a.i == 0


def test_dynamic_metamodel_entry_point():
    A = EClass('A')

    @A.behavior
    def my_fun(self, i):
        return i + 1

    a = A()
    x = 1
    with pytest.raises(NotImplementedError):
        run(a)

    # We add the behavior *after* the instance creation
    @main
    @A.behavior
    def entry_point(self, i=0):
        return self.my_fun(i)

    y = run(a, x)
    assert y == x + 1


def test_dynamic_metamodel_behavior_injection_newdecorator():
    A = EClass('A')

    @behavior(A)
    def my_fun(self):
        return True

    @behavior(A)
    def __init__(self, i=15):
        self.i = i

    a = A()
    assert a.my_fun() is True
    assert a.i == 15

    a = A(i=0)
    assert a.i == 0


def test_static_metamodel_behavior_injection_newdecorator():
    @EMetaclass
    class A(object):
        ...

    @behavior(A)
    def my_fun(self, stuff):
        """mydoc"""
        return stuff + 5

    @behavior(A)
    def __init__(self, i=15):
        self.i = i

    a = A()
    assert a.my_fun(0) == 5
    assert a.i == 15

    a = A(i=0)
    assert a.i == 0
    assert A.my_fun.__doc__ == "mydoc"
