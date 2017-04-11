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

    def __init__(self, name_=None, age_=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()
        if name_ is not None:
            self.name = name_
        if age_ is not None:
            self.age = age_


class Library(EObject, metaclass=MetaEClass):
    name = EAttribute(eType=EString)
    address = EAttribute(eType=EString)
    employees = EReference(upper=-1, containment=True)
    writers = EReference(upper=-1, containment=True)
    books = EReference(upper=-1, containment=True)

    def __init__(self, name_=None, address_=None, employees_=None, writers_=None, books_=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()
        if name_ is not None:
            self.name = name_
        if address_ is not None:
            self.address = address_
        if employees_:
            self.employees.extend(employees_)
        if writers_:
            self.writers.extend(writers_)
        if books_:
            self.books.extend(books_)


class Writer(EObject, metaclass=MetaEClass):
    name = EAttribute(eType=EString)
    books = EReference(upper=-1)

    def __init__(self, name_=None, books_=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()
        if name_ is not None:
            self.name = name_
        if books_:
            self.books.extend(books_)


class Book(EObject, metaclass=MetaEClass):
    title = EAttribute(eType=EString)
    pages = EAttribute(eType=EInt)
    category = EAttribute(eType=BookCategory)
    authors = EReference(upper=-1)

    def __init__(self, title_=None, pages_=None, category_=None, authors_=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()
        if title_ is not None:
            self.title = title_
        if pages_ is not None:
            self.pages = pages_
        if category_ is not None:
            self.category = category_
        if authors_:
            self.authors.extend(authors_)
