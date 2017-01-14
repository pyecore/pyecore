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


def test_static_eoperation():
    assert len(simple.A.eClass.eOperations) == 1
    assert simple.A.eClass.eOperations != []
    operation = simple.A.eClass.eOperations[0]
    assert operation.name == simple.A.a_eoperation.__name__
    assert len(operation.eParameters) == 2


def test_static_eoperation_exec():
    a = simple.A()
    a.name = 'mya'
    assert a.a_eoperation(3) == 'mya_3'


def test_static_skipEOperation():
    fun_names = [x.name for x in simple.A.eClass.eOperations]
    assert 'another_one' not in fun_names
    assert 'other_operation' not in fun_names
