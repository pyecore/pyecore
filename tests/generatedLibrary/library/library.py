from pyecore.ecore import *
import pyecore.ecore as Ecore

name = 'library'
nsURI = 'http://emf.wikipedia.org/2011/Library'
nsPrefix = 'lib'

eClass = Ecore.EPackage(name=name, nsURI=nsURI, nsPrefix=nsPrefix)
eSubpackages = []
eSuperPackage = None


BookCategory = EEnum('BookCategory', literals=['ScienceFiction','Biographie','Mistery',])


class Employee(EObject, metaclass=MetaEClass):

    name = EAttribute(eType=EString)
    age = EAttribute(eType=EInteger)

    def __init__(self):
        super().__init__()


class Library(EObject, metaclass=MetaEClass):

    name = EAttribute(eType=EString)
    address = EAttribute(eType=EString)
    employees = EReference(upper=-1, containment=True)
    writers = EReference(upper=-1, containment=True)
    books = EReference(upper=-1, containment=True)

    def __init__(self):
        super().__init__()


class Writer(EObject, metaclass=MetaEClass):

    name = EAttribute(eType=EString)
    books = EReference(upper=-1)

    def __init__(self):
        super().__init__()


class Book(EObject, metaclass=MetaEClass):

    title = EAttribute(eType=EString)
    pages = EAttribute(eType=EInteger)
    category = EAttribute(eType=BookCategory)
    authors = EReference(upper=-1)

    def __init__(self):
        super().__init__()
