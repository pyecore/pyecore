import sys
import pytest
import wikilib
import pyecore.ecore as Ecore


def test_get_existing_EClassifier():
    assert wikilib.getEClassifier('Book')
    assert wikilib.getEClassifier('BookCategory')


def test_get_nonexisting_EClassifier():
    assert not wikilib.getEClassifier('NBook')


def test_create_book():
    book = wikilib.Book()
    assert book and isinstance(book, Ecore.EObject)
    assert book.title is None
    assert book.category is wikilib.BookCategory.ScienceFiction


def test_create_writer():
    smith = wikilib.Writer()
    assert smith and isinstance(smith, Ecore.EObject)
    assert smith.name is None
    assert smith.books == []


def test_book_defaultvalue():
    book = wikilib.Book()
    assert book.category is wikilib.BookCategory.ScienceFiction
    assert book.pages == 0
    assert book.title is Ecore.EString.default_value


def test_link_writer2book():
    book = wikilib.Book()
    smith = wikilib.Writer()
    smith.books.append(book)
    assert smith.books and smith.books[0] is book
    assert book.authors and book.authors[0] is smith


def test_link_writer2manybooks():
    book1 = wikilib.Book()
    book2 = wikilib.Book()
    smith = wikilib.Writer()
    smith.books.extend([book1, book2])
    assert smith.books and book1 in smith.books and book2 in smith.books
    assert book1.authors and smith in book1.authors
    assert book2.authors and smith in book2.authors


def test_wikilib_econtents():
    smith = wikilib.Writer()
    book = wikilib.Book()
    lib = wikilib.Library()
    lib.writers.append(smith)
    lib.books.append(book)
    assert smith in lib.eContents
    assert book in lib.eContents


def test_instance_eisset():
    smith = wikilib.Writer()
    assert smith._isset == set()
    smith.name = 'SmithIsMyName'
    assert wikilib.Writer.name in smith._isset
    assert smith.eIsSet(wikilib.Writer.name)
    assert smith.eIsSet('name')
    smith.name = None
    assert wikilib.Writer.name in smith._isset
    assert smith.eIsSet(wikilib.Writer.name)
    assert smith.eIsSet('name')


def test_instance_urifragment():
    lib = wikilib.Library()
    assert lib.eURIFragment() == '/'
    smith = wikilib.Writer()
    lib.writers.append(smith)
    assert smith.eURIFragment() == '//@writers.0'


def test_wikilib_epackage():
    assert wikilib.Book.eClass.ePackage is wikilib.eClass
    assert sys.modules[wikilib.Book.__module__] is wikilib.eModule
    assert wikilib.BookCategory.eContainer() is wikilib.eClass


def test_wikilib_eroot():
    lib = wikilib.Library()
    smith = wikilib.Writer()
    lib.writers.append(smith)
    assert smith.eContainer() is lib
    assert smith.eRoot() is lib
    assert wikilib.Library.eClass.eRoot() is wikilib.eClass


def test_static_eclass_class():
    lib = wikilib.Library()
    assert lib.eClass.python_class is wikilib.Library
    assert wikilib.Library.eClass.python_class.eClass is wikilib.Library.eClass
