import sys
import pytest
import library
import pyecore.ecore as Ecore


def test_meta_attribute_access():
    assert isinstance(library.Book.category, Ecore.EAttribute)
    attribute = library.Book.category
    assert attribute.name == 'category'
    assert attribute.upperBound == 1
    assert attribute.lowerBound == 0
    assert isinstance(attribute.eType, Ecore.EDataType)
    assert attribute.eType is library.BookCategory


def test_meta_reference_access():
    assert isinstance(library.Book.authors, Ecore.EReference)
    reference = library.Book.authors
    assert reference.name == 'authors'
    assert reference.upperBound == -1
    assert reference.lowerBound == 0
    assert reference.eType is library.Writer


def test_get_existing_EClassifier_generated():
    assert library.getEClassifier('Book')
    assert library.getEClassifier('BookCategory')


def test_get_nonexisting_EClassifier_generated():
    assert not library.getEClassifier('NBook')


def test_create_book_generated():
    book = library.Book()
    assert book and isinstance(book, Ecore.EObject)
    assert book.title is None
    assert book.category is library.BookCategory.ScienceFiction


def test_create_writer_generated():
    smith = library.Writer()
    assert smith and isinstance(smith, Ecore.EObject)
    assert smith.name is None
    assert smith.books == []


def test_book_defaultvalue_generated():
    book = library.Book()
    assert book.category is library.BookCategory.ScienceFiction
    assert book.pages == 0
    assert book.title is Ecore.EString.default_value


def test_link_writer2book_generated():
    book = library.Book()
    smith = library.Writer()
    smith.books.append(book)
    assert smith.books and smith.books[0] is book
    assert book.authors and book.authors[0] is smith


def test_link_writer2manybooks_generated():
    book1 = library.Book()
    book2 = library.Book()
    smith = library.Writer()
    smith.books.extend([book1, book2])
    assert smith.books and book1 in smith.books and book2 in smith.books
    assert book1.authors
    assert book2.authors


def test_library_econtents_generated():
    smith = library.Writer()
    book = library.Book()
    lib = library.Library()
    lib.writers.append(smith)
    lib.books.append(book)
    assert smith in lib.eContents
    assert book in lib.eContents


def test_instance_eisset_generated():
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


def test_instance_urifragment_generated():
    lib = library.Library()
    assert lib.eURIFragment() == '/'
    smith = library.Writer()
    lib.writers.append(smith)
    assert smith.eURIFragment() == '//@writers.0'


# def test_library_epackage():
#     assert library.Book.eClass.ePackage is library.eClass
#     assert sys.modules[library.Book.__module__] is library.eModule
#     assert library.BookCategory.eContainer() is library.eModule


def test_library_eroot_generated():
    lib = library.Library()
    smith = library.Writer()
    lib.writers.append(smith)
    assert smith.eContainer() is lib
    assert smith.eRoot() is lib
    assert library.Library.eClass.eRoot() is library.eClass


def test_static_eclass_class_generated():
    lib = library.Library()
    assert lib.eClass.python_class is library.Library
    assert library.Library.eClass.python_class.eClass is library.Library.eClass
