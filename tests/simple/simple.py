from functools import partial
import pyecore.ecore as Ecore
from pyecore.ecore import EObject, EAttribute, EString, EEnum, EReference, \
                          MetaEClass, EInteger, abstract


name = 'simple'
nsPrefix = 'simple'
nsURI = 'http://simple/1.0'

eClass = Ecore.EPackage(name=name, nsPrefix=nsPrefix, nsURI=nsURI)


@abstract
class AbstractA(EObject, metaclass=MetaEClass):
    name = EAttribute(eType=EString)


class A(AbstractA):
    def a_eoperation(self, i):
        return self.name + '_' + str(i)

    def other_operation(x, y):
        pass

    def another_one():
        pass

class B(EObject, metaclass=MetaEClass):
    a = EReference(eType=AbstractA)
