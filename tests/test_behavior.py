import pytest
from pyecore.ecore import *
import pyecore.behavior


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
