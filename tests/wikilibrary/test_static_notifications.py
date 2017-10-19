import pytest
import library as lib
from pyecore.notification import EObserver, Kind


class LastNotification(EObserver):
    def __init__(self, notifier=None):
        super(LastNotification, self).__init__(notifier=notifier)
        self.notification = None

    def notifyChanged(self, notification):
        self.notification = notification


def test_notification_static_set():
    library = lib.Library()
    o = LastNotification(library)
    library.name = 'SuperLib'
    notif = o.notification
    assert notif.kind is Kind.SET
    assert notif.new == 'SuperLib'
    assert notif.old is None
    assert notif.feature is lib.Library.name


def test_notification_static_unset():
    library = lib.Library()
    o = LastNotification(library)
    library.name = 'SuperLib'
    library.name = None
    notif = o.notification
    assert notif.kind is Kind.UNSET
    assert notif.old == 'SuperLib'
    assert notif.feature is lib.Library.name


def test_notification_static_add():
    smith = lib.Writer()
    b1 = lib.Book()
    o = LastNotification(smith)
    o2 = LastNotification(b1)
    b1.authors.append(smith)
    n1 = o.notification
    n2 = o2.notification
    assert n1.kind is Kind.ADD
    assert n1.new is b1
    assert n1.feature is lib.Writer.books
    assert n2.kind is Kind.ADD
    assert n2.new is smith
    assert n2.feature is lib.Book.authors
