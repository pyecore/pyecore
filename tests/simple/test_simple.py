import pytest
import simple
import pyecore.ecore as Ecore


def test_static_create_abstract():
    with pytest.raises(TypeError):
        simple.AbstractA()


def test_static_create_simple():
    b = simple.B()
    assert b.a is None
