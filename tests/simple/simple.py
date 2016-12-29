from functools import partial
import pyecore.ecore as Ecore
from pyecore.ecore import EObject, EAttribute, EString, EEnum, EReference, \
                          MetaEClass, EInteger, abstract


nsPrefix = 'simple'
nsURI = 'http://simple/1.0'


@abstract
class AbstractA(EObject, metaclass=MetaEClass):
    name = EAttribute(eType=EString)

    def __init__(self):
        pass


class A(AbstractA):
    def __init__(self):
        pass


class B(EObject, metaclass=MetaEClass):
    a = EReference(eType=AbstractA)

    def __init__(self):
        pass


eClassifiers = Ecore.Core.compute_eclass(__name__)
getEClassifier = partial(Ecore.getEClassifier, searchspace=eClassifiers)
