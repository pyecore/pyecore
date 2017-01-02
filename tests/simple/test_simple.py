import pytest
import simple
import pyecore.ecore as Ecore


def test_static_create_abstract():
    with pytest.raises(TypeError):
        simple.AbstractA()


def test_static_create_simple():
    b = simple.B()
    assert b.a is None


def test_static_eallsupertypes():
    a = simple.A()
    assert simple.AbstractA.eClass in a.eClass.eAllSuperTypes()
