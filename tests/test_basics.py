import pytest
from pyecore.ecore import *

def test_ecore_URI():
    assert nsURI == 'http://www.eclipse.org/emf/2002/Ecore'


def test_get_existing_EClassifier():
    assert getEClassifier('EClass')


def test_get_nonexisting_EClassifier():
    assert not getEClassifier('EEClass')


def test_ecore_isinstance_none():
    assert EcoreUtils.isinstance(None, EClass)
