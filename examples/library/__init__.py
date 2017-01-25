import pyecore.ecore as Ecore
from .library import getEClassifier, eClassifiers
from .library import Employee, Library, Writer, Book, BookCategory
from . import library

__all__ = ['Employee', 'Library', 'Writer', 'Book', 'BookCategory']

name = 'library'
nsURI = 'http://emf.wikipedia.org/2011/Library'
nsPrefix = 'lib'

eClass = Ecore.EPackage(name=name, nsURI=nsURI, nsPrefix=nsPrefix)

eSubpackages = []
eSuperPackage = None


# Non opposite EReferences
Library.employees.eType = Employee
Library.writers.eType = Writer
Library.books.eType = Book

# opposite EReferences
Writer.books.eType = Book
Book.authors.eType = Writer
Book.authors.eOpposite = Writer.books


# Manage all other EClassifiers (EEnum, EDatatypes...)
otherClassifiers = [BookCategory]
for classif in otherClassifiers:
    eClassifiers[classif.name] = classif
    classif._container = library

for classif in eClassifiers.values():
    eClass.eClassifiers.append(classif.eClass)

for subpack in eSubpackages:
    eClass.eSubpackages.append(subpack.eClass)
