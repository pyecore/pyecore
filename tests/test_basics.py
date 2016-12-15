import pytest
import pyecore.ecore as Ecore

def test_ecore_URI():
    assert Ecore.nsURI == 'http://www.eclipse.org/emf/2002/Ecore'


def test_get_existing_EClassifier():
    assert Ecore.getEClassifier('EClass')


def test_get_nonexisting_EClassifier():
    assert not Ecore.getEClassifier('EEClass')
