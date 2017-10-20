"""
Library example from the EMF wikipedia page:
https://fr.wikipedia.org/wiki/Eclipse_Modeling_Framework#/media/File:EMF_based_meta-model.png
The static metamodel had been produced by hand in this example
"""
import sys
import pyecore.ecore as Ecore
from pyecore.ecore import EObject, EAttribute, EString, EEnum, EReference, \
                          MetaEClass, EInteger

name = 'library'
nsPrefix = 'lib'
nsURI = 'http://emf.wikipedia.org/2011/Library'

# Do not remove
eClass = Ecore.EPackage(name=name, nsURI=nsURI, nsPrefix=nsPrefix)

BookCategory = EEnum('BookCategory', literals=['ScienceFiction',
                                               'Biography',
                                               'Mistery'])


class Book(EObject):
    __metaclass__ = MetaEClass
    title = EAttribute(eType=EString)
    pages = EAttribute(eType=EInteger)
    category = EAttribute(eType=BookCategory,
                          default_value=BookCategory.ScienceFiction)

    def __init__(self):
        pass


class Writer(EObject):
    __metaclass__ = MetaEClass
    name = EAttribute(eType=EString)
    books = EReference(eType=Book, lower=1, upper=-1)

    def __init__(self):
        pass


Book.authors = EReference('authors', Writer, lower=1, upper=-1,
                          eOpposite=Writer.books)
Book.eClass.eStructuralFeatures.append(Book.authors)


class Employee(EObject):
    __metaclass__ = MetaEClass
    name = EAttribute(eType=EString)
    age = EAttribute(eType=EInteger)

    def __init__(self):
        pass


class Library(EObject):
    __metaclass__ = MetaEClass
    name = EAttribute(eType=EString)
    address = EAttribute(eType=EString)
    employees = EReference(eType=Employee, upper=-1, containment=True)
    writers = EReference(eType=Writer, upper=-1, containment=True)
    books = EReference(eType=Book, upper=-1, containment=True)

    def __init__(self):
        pass


# ==
#   Warning, do not remove
# ==
eURIFragment = Ecore.default_eURIFragment
eModule = sys.modules[__name__]
otherClassifiers = [BookCategory]
for classif in otherClassifiers:
    eClassifiers[classif.name] = classif
    classif._container = eModule

for classif in eClassifiers.values():
    eClass.eClassifiers.append(classif.eClass)
