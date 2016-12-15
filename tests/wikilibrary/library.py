from functools import partial
import pyecore.ecore as Ecore
from pyecore.ecore import EObject, EAttribute, EString, EEnum, EReference, \
                          MetaEClass, EInteger

nsPrefix = 'lib'
nsURI = 'http://emf.wikipedia.org/2011/Library'

BookCategory = EEnum('BookCategory', literals=['ScienceFiction',
                                               'Biography',
                                               'Mistery'])


class Book(EObject, metaclass=MetaEClass):
    title = EAttribute(eType=EString)
    pages = EAttribute(eType=EInteger)
    category = EAttribute(eType=BookCategory,
                          default_value=BookCategory.ScienceFiction)

    def __init__(self):
        pass


class Writer(EObject, metaclass=MetaEClass):
    name = EAttribute(eType=EString)
    books = EReference(eType=Book, lower=1, upper=-1)

    def __init__(self):
        pass


Book.authors = EReference('authors', Writer, lower=1, upper=-1,
                          eOpposite=Writer.books)
Book.eClass.eReferences.append(Book.authors)


class Employee(EObject, metaclass=MetaEClass):
    name = EAttribute(eType=EString)
    age = EAttribute(eType=EInteger)

    def __init__(self):
        pass


class Library(EObject, metaclass=MetaEClass):
    name = EAttribute(eType=EString)
    address = EAttribute(eType=EString)
    employees = EReference(eType=Employee, upper=-1, containment=True)
    writers = EReference(eType=Writer, upper=-1, containment=True)
    books = EReference(eType=Book, upper=-1, containment=True)

    def __init__(self):
        pass

__eClassifiers = Ecore.Core.compute_eclass(__name__)
getEClassifier = partial(Ecore.getEClassifier, searchspace=__eClassifiers)
