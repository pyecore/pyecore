"""Copy of the original static library module tests."""
import os
import shutil
import sys

import pytest

import pyecore.ecore as Ecore
from pyecore.resources import ResourceSet, URI
from pyecore.utils import DynamicEPackage
from pygen.ecore import EcoreGenerator


@pytest.fixture('module', autouse=True)
def cwd_module_dir():
    # change cwd to this module's directory:
    cwd = os.getcwd()
    os.chdir(os.path.dirname(__file__))
    yield

    # reset after module goes out of scope:
    os.chdir(cwd)


@pytest.fixture(scope='module')
def pygen_output_dir():
    path = os.path.join('output', 'pygen2')
    shutil.rmtree(path, ignore_errors=True)
    original_sys_path = sys.path
    sys.path.append(path)
    yield path
    sys.path.remove(path)
    shutil.rmtree(path, ignore_errors=False)


@pytest.fixture(scope='module')
def generated_library(pygen_output_dir):
    rset = ResourceSet()
    resource = rset.get_resource(URI('../../examples/library.ecore'))
    library_model = resource.contents[0]
    rset.metamodel_registry[library_model.nsURI] = library_model
    generator = EcoreGenerator()
    generator.generate(library_model, pygen_output_dir)
    import library as library_gen
    return library_gen


def test_meta_attribute_access(generated_library):
    assert isinstance(generated_library.Book.category, Ecore.EAttribute)
    attribute = generated_library.Book.category
    assert attribute.name == 'category'
    assert attribute.upperBound == 1
    assert attribute.lowerBound == 0
    assert isinstance(attribute.eType, Ecore.EDataType)
    assert attribute.eType is generated_library.BookCategory


def test_meta_reference_access(generated_library):
    assert isinstance(generated_library.Book.authors, Ecore.EReference)
    reference = generated_library.Book.authors
    assert reference.name == 'authors'
    assert reference.upperBound == -1
    assert reference.lowerBound == 0
    assert reference.eType is generated_library.Writer


def test_get_existing_EClassifier_generated(generated_library):
    assert generated_library.getEClassifier('Book')
    assert generated_library.getEClassifier('BookCategory')


def test_get_nonexisting_EClassifier_generated(generated_library):
    assert not generated_library.getEClassifier('NBook')


def test_create_book_generated(generated_library):
    book = generated_library.Book()
    assert book and isinstance(book, Ecore.EObject)
    assert book.title is None
    assert book.category is generated_library.BookCategory.ScienceFiction


def test_create_writer_generated(generated_library):
    smith = generated_library.Writer()
    assert smith and isinstance(smith, Ecore.EObject)
    assert smith.name is None
    assert smith.books == []


def test_book_defaultvalue_generated(generated_library):
    book = generated_library.Book()
    assert book.category is generated_library.BookCategory.ScienceFiction
    assert book.pages == 0
    assert book.title is Ecore.EString.default_value


def test_link_writer2book_generated(generated_library):
    book = generated_library.Book()
    smith = generated_library.Writer()
    smith.books.append(book)
    assert smith.books and smith.books[0] is book
    assert book.authors and book.authors[0] is smith


def test_link_writer2manybooks_generated(generated_library):
    book1 = generated_library.Book()
    book2 = generated_library.Book()
    smith = generated_library.Writer()
    smith.books.extend([book1, book2])
    assert smith.books and book1 in smith.books and book2 in smith.books
    assert book1.authors
    assert book2.authors


def test_library_econtents_generated(generated_library):
    smith = generated_library.Writer()
    book = generated_library.Book()
    lib = generated_library.Library()
    lib.writers.append(smith)
    lib.books.append(book)
    assert smith in lib.eContents
    assert book in lib.eContents


def test_instance_eisset_generated(generated_library):
    smith = generated_library.Writer()
    assert smith._isset == set()
    smith.name = 'SmithIsMyName'
    assert generated_library.Writer.name in smith._isset
    assert smith.eIsSet(generated_library.Writer.name)
    assert smith.eIsSet('name')
    smith.name = None
    assert generated_library.Writer.name in smith._isset
    assert smith.eIsSet(generated_library.Writer.name)
    assert smith.eIsSet('name')


def test_instance_urifragment_generated(generated_library):
    lib = generated_library.Library()
    assert lib.eURIFragment() == '/'
    smith = generated_library.Writer()
    lib.writers.append(smith)
    assert smith.eURIFragment() == '//@writers.0'


def test_library_eroot_generated(generated_library):
    lib = generated_library.Library()
    smith = generated_library.Writer()
    lib.writers.append(smith)
    assert smith.eContainer() is lib
    assert smith.eRoot() is lib
    assert generated_library.Library.eClass.eRoot() is generated_library.eClass


def test_static_eclass_class_generated(generated_library):
    lib = generated_library.Library()
    assert lib.eClass.python_class is generated_library.Library
    assert generated_library.Library.eClass.python_class.eClass is generated_library.Library.eClass


def test_static_init_single_attribute(generated_library):
    smith = generated_library.Writer(name='Smith')
    assert smith.name == 'Smith'
    assert smith.eIsSet('name')


def test_static_init_many_attributes(generated_library):
    book = generated_library.Book(pages=10, title='Python Roxx')
    assert book.title == 'Python Roxx'
    assert book.pages == 10


def test_static_init_single_reference(generated_library):
    smith = generated_library.Writer(name='Smith')
    book = generated_library.Book(title='Python Roxx', pages=10, authors=[smith])
    assert smith in book.authors
    assert book in smith.books


def test_static_init_single_attribute_bad_type(generated_library):
    with pytest.raises(Ecore.BadValueError):
        generated_library.Writer(name=4)


def test_static_init_bad_argument(generated_library):
    with pytest.raises(AttributeError):
        generated_library.Book(unknown=None)


def test_static_init_dynamic_epackage_bad_value(generated_library):
    with pytest.raises(Ecore.BadValueError):
        DynamicEPackage(generated_library)
