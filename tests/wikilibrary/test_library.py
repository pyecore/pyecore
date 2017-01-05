import sys
import pytest
import library
import pyecore.ecore as Ecore


def test_get_existing_EClassifier():
    assert library.getEClassifier('Book')
    assert library.getEClassifier('BookCategory')


def test_get_nonexisting_EClassifier():
    assert not library.getEClassifier('NBook')


def test_create_book():
    book = library.Book()
    assert book and isinstance(book, Ecore.EObject)
    assert book.title is None
    assert book.category is library.BookCategory.ScienceFiction


def test_create_writer():
    smith = library.Writer()
    assert smith and isinstance(smith, Ecore.EObject)
    assert smith.name is None
    assert smith.books == []


def test_link_writer2book():
    book = library.Book()
    smith = library.Writer()
    smith.books.append(book)
    assert smith.books and smith.books[0] is book
    assert book.authors and book.authors[0] is smith


def test_link_writer2manybooks():
    book1 = library.Book()
    book2 = library.Book()
    smith = library.Writer()
    smith.books.extend([book1, book2])
    assert smith.books and book1 in smith.books and book2 in smith.books
    assert book1.authors and smith in book1.authors
    assert book2.authors and smith in book2.authors


def test_library_econtents():
    smith = library.Writer()
    book = library.Book()
    lib = library.Library()
    lib.writers.append(smith)
    lib.books.append(book)
    assert smith in lib.eContents
    assert book in lib.eContents


def test_instance_eisset():
    smith = library.Writer()
    assert smith._isset == set()
    smith.name = 'SmithIsMyName'
    assert library.Writer.name in smith._isset
    assert smith.eIsSet(library.Writer.name)
    assert smith.eIsSet('name')
    smith.name = None
    assert library.Writer.name in smith._isset
    assert smith.eIsSet(library.Writer.name)
    assert smith.eIsSet('name')


def test_instance_urifragment():
    lib = library.Library()
    assert lib.eURIFragment() == '/'
    smith = library.Writer()
    lib.writers.append(smith)
    assert smith.eURIFragment() == '//@writers.0'


def test_library_epackage():
    assert library.Book.eClass.ePackage is library.eClass
    assert sys.modules[library.Book.__module__] is library.eModule
    assert library.BookCategory.eContainer() is library.eModule


def test_library_eroot():
    lib = library.Library()
    smith = library.Writer()
    lib.writers.append(smith)
    assert smith.eContainer() is lib
    assert smith.eRoot() is lib
    assert library.Library.eClass.eRoot() is library.eClass
