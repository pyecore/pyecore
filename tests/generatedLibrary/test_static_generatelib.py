import sys
import pytest
import library
from pyecore.ecore import BadValueError
import pyecore.ecore as Ecore
from pyecore.utils import DynamicEPackage


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


def test_library_epackage():
    assert library.Book.eClass.ePackage is library.eClass
    assert library.BookCategory.eContainer() is library.eClass


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


def test_static_init_single_attribute():
    smith = library.Writer(name='Smith')
    assert smith.name == 'Smith'
    assert smith.eIsSet('name')


def test_static_init_many_attributes():
    book = library.Book(pages=10, title='Python Roxx')
    assert book.title == 'Python Roxx'
    assert book.pages == 10


def test_static_init_single_reference():
    smith = library.Writer(name='Smith')
    book = library.Book(title='Python Roxx', pages=10, authors=[smith])
    assert smith in book.authors
    assert book in smith.books


def test_static_init_single_attribute_bad_type():
    with pytest.raises(BadValueError):
        library.Writer(name=4)


def test_static_init_single_reference_bad_type():
    with pytest.raises(BadValueError):
        library.Book(authors=[library.Book()])


def test_static_init_bad_argument():
    with pytest.raises(AttributeError):
        library.Book(unknown=None)


def test_static_init_dynamicEPackage_bad_value():
    with pytest.raises(BadValueError):
        DynamicEPackage(library)


def test_static_edatatype_epackage():
    assert library.BookCategory.ePackage is library.Writer.eClass.ePackage


def test_static_eclass_name():
    assert library.Book.eClass.__name__ == 'Book'
