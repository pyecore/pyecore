from .library import getEClassifier, eClassifiers
from .library import name, nsURI, nsPrefix, eClass
from .library import Employee, Library, Writer, Book, BookCategory
from . import library

__all__ = ['Employee', 'Library', 'Writer', 'Book', 'BookCategory']

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
    classif.ePackage = eClass

for classif in eClassifiers.values():
    eClass.eClassifiers.append(classif.eClass)

for subpack in eSubpackages:
    eClass.eSubpackages.append(subpack.eClass)
