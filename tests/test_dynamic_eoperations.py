import pytest
from pyecore.ecore import *
import inspect


def test_dynamic_eoperation_0params():
    op1 = EOperation('op1')
    A = EClass('A')
    A.eOperations.append(op1)
    a = A()
    assert a.op1  # op1 exists
    assert inspect.isfunction(a.op1) or inspect.ismethod(a.op1)
    with pytest.raises(NotImplementedError):
        a.op1()


def test_dynamic_eoperation_1required():
    op1 = EOperation('op1')
    p1 = EParameter('p1', eType=EString, required=True)
    op1.eParameters.append(p1)
    assert p1.eContainer() is op1

    A = EClass('A')
    A.eOperations.append(op1)
    a = A()
    assert a.op1
    with pytest.raises(TypeError):  # parameter is missing
        a.op1()
    with pytest.raises(NotImplementedError):
        a.op1('mystring')


def test_dynamic_eoperation_1optional():
    op1 = EOperation('op1')
    p1 = EParameter('p1', eType=EString)
    op1.eParameters.append(p1)
    A = EClass('A')
    A.eOperations.append(op1)
    a = A()
    assert a.op1
    with pytest.raises(NotImplementedError):
        a.op1()
    with pytest.raises(NotImplementedError):
        a.op1('mystring')
    with pytest.raises(NotImplementedError):
        a.op1(p1='mystring')


def test_dynamic_eoperation_1required_2optionals():
    op1 = EOperation('op1')
    p1 = EParameter('p1', eType=EString, required=True)
    p2 = EParameter('p2', eType=EInteger)
    p3 = EParameter('p3', eType=EStringToStringMapEntry)
    op1.eParameters.extend([p1, p2, p3])
    A = EClass('A')
    A.eOperations.append(op1)
    a = A()
    assert a.op1
    with pytest.raises(TypeError):  # missing p1 parameter
        a.op1()
    with pytest.raises(NotImplementedError):
        a.op1('mystring')
    with pytest.raises(NotImplementedError):
        a.op1(p1='mystring')
    with pytest.raises(NotImplementedError):
        a.op1('mystring', p2=4)
    with pytest.raises(NotImplementedError):
        a.op1('mystring', p2=4, p3={1: 'test'})
