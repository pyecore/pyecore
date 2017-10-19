import pytest
from pyecore.ecore import *
from pyecore.notification import EObserver, Kind


class ObserverCounter(EObserver):
    def __init__(self, notifier=None):
        super(ObserverCounter, self).__init__(notifier=notifier)
        self.calls = 0

    def notifyChanged(self, notification):
        self.calls += 1
        self.kind = notification.kind
        self.feature = notification.feature


def test_notification_add_onecall():
    root = EPackage(name='test')
    A = EClass('A')
    o1 = ObserverCounter(root)
    o2 = ObserverCounter(A)
    root.eClassifiers.append(A)
    assert o1.calls == 1
    assert o1.kind == Kind.ADD
    assert o1.feature is EPackage.eClassifiers
    assert o2.calls == 1
    assert o2.kind == Kind.SET
    assert o2.feature is EClassifier.ePackage


def test_notification_remove_onecall():
    root = EPackage(name='test')
    A = EClass('A')
    root.eClassifiers.append(A)

    o1 = ObserverCounter(root)
    o2 = ObserverCounter(A)
    root.eClassifiers.remove(A)
    assert o1.calls == 1
    assert o1.kind == Kind.REMOVE
    assert o1.feature is EPackage.eClassifiers
    assert o2.calls == 1
    assert o2.kind == Kind.UNSET
    assert o2.feature is EClassifier.ePackage


def test_notification_delete_onecall():
    root = EPackage(name='test')
    A = EClass('A')
    root.eClassifiers.append(A)

    o1 = ObserverCounter(root)
    o2 = ObserverCounter(A)
    A.delete()
    assert o1.calls == 1
    assert o1.kind == Kind.REMOVE
    assert o1.feature is EPackage.eClassifiers
    assert o2.calls == 1
    assert o2.kind == Kind.UNSET
    assert o2.feature is EClassifier.ePackage
