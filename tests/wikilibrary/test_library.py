import pytest
import library
import pyecore.ecore as Ecore


def test_get_existing_EClassifier():
    assert library.getEClassifier('Book')


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
    assert smith.books and smith.books[0] is book1 and smith.books[1] is book2
    assert book1.authors and book1.authors[0] is smith
    assert book2.authors and book2.authors[0] is smith
