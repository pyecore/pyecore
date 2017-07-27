import pytest
from pyecore.ecore import *
import pyecore.ecore as ecore
from ordered_set import OrderedSet


def test__EModelElement_extension():
    A = EClass('A', superclass=(EModelElement.eClass))
    a = A()
    assert a.eAnnotations == OrderedSet()

    annotation = EAnnotation(source='testAnnot')
    annotation.details['test'] = 'value'
    a.eAnnotations.append(annotation)
    assert len(a.eAnnotations) == 1
    assert a.getEAnnotation('testAnnot') is annotation
    assert a.getEAnnotation('testAnnot').details['test'] == 'value'


def test__EClass_extension():
    SuperEClass = EClass('SuperEClass', superclass=(EClass.eClass,))
    A = SuperEClass(name='A')
    assert isinstance(A, EClass)

    a = A()
    assert isinstance(a, EObject)
    assert a.eClass is A


def test__EClass_modification():
    EClass.new_feature = EAttribute('new_feature', EInt)
    A = EClass('A')
    assert A.new_feature == 0

    A.new_feature = 5
    assert A.new_feature == 5

    with pytest.raises(BadValueError):
        A.new_feature = 'a'
