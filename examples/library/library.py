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


class Employee(EObject):
    __metaclass__ = MetaEClass
    name = EAttribute(eType=EString)
    age = EAttribute(eType=EInt)

    def __init__(self, name=None, age=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super(Employee, self).__init__()
        if name is not None:
            self.name = name
        if age is not None:
            self.age = age


class Library(EObject):
    __metaclass__ = MetaEClass
    name = EAttribute(eType=EString)
    address = EAttribute(eType=EString)
    employees = EReference(upper=-1, containment=True)
    writers = EReference(upper=-1, containment=True)
    books = EReference(upper=-1, containment=True)

    def __init__(self, name=None, address=None, employees=None, writers=None, books=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super(Library, self).__init__()
        if name is not None:
            self.name = name
        if address is not None:
            self.address = address
        if employees:
            self.employees.extend(employees)
        if writers:
            self.writers.extend(writers)
        if books:
            self.books.extend(books)


class Writer(EObject):
    __metaclass__ = MetaEClass
    name = EAttribute(eType=EString)
    books = EReference(upper=-1)

    def __init__(self, name=None, books=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super(Writer, self).__init__()
        if name is not None:
            self.name = name
        if books:
            self.books.extend(books)


class Book(EObject):
    __metaclass__ = MetaEClass
    title = EAttribute(eType=EString)
    pages = EAttribute(eType=EInt)
    category = EAttribute(eType=BookCategory)
    authors = EReference(upper=-1)

    def __init__(self, title=None, pages=None, category=None, authors=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super(Book, self).__init__()
        if title is not None:
            self.title = title
        if pages is not None:
            self.pages = pages
        if category is not None:
            self.category = category
        if authors:
            self.authors.extend(authors)
