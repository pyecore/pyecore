from functools import partial
import pyecore.ecore as Ecore
from pyecore.ecore import *

name = 'library'
nsURI = 'http://emf.wikipedia.org/2011/Library'
nsPrefix = 'lib'

eClass = EPackage(name=name, nsURI=nsURI, nsPrefix=nsPrefix)

eClassifiers = {}
getEClassifier = partial(Ecore.getEClassifier, searchspace=eClassifiers)


BookCategory = EEnum('BookCategory', literals=['ScienceFiction', 'Biographie', 'Mistery'])  # noqa


class Employee(EObject, metaclass=MetaEClass):
    name = EAttribute(eType=EString)
    age = EAttribute(eType=EInt)


class Library(EObject, metaclass=MetaEClass):
    name = EAttribute(eType=EString)
    address = EAttribute(eType=EString)
    employees = EReference(upper=-1, containment=True)
    writers = EReference(upper=-1, containment=True)
    books = EReference(upper=-1, containment=True)


class Writer(EObject, metaclass=MetaEClass):
    name = EAttribute(eType=EString)
    books = EReference(upper=-1)


class Book(EObject, metaclass=MetaEClass):
    title = EAttribute(eType=EString)
    pages = EAttribute(eType=EInt)
    category = EAttribute(eType=BookCategory)
    authors = EReference(upper=-1)
