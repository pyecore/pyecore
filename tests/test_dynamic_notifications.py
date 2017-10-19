import pytest
from pyecore.ecore import *
from pyecore.notification import EObserver, Kind

def assert_wrap(condition):
    assert condition

@pytest.fixture(scope='module')
def lib():
    NamedElement = EClass('NamedElement', abstract=True)
    NamedElement.eStructuralFeatures.append(EAttribute('name', EString))
    NamedElement.eStructuralFeatures.append(EAttribute('level', EInteger))
    Root = EClass('Root')
    Root.eStructuralFeatures.append(EReference('namedElements', eType=NamedElement, containment=True, upper=-1, unique=False))
    Root.eStructuralFeatures.append(EReference('ne_oset', eType=NamedElement, containment=True, upper=-1))
    Root.eStructuralFeatures.append(EReference('ne_set', eType=NamedElement, containment=True, upper=-1, ordered=False))

    A = EClass('A', superclass=NamedElement)
    B = EClass('B', superclass=NamedElement)
    inner_ref = EReference('inner', eType=NamedElement, containment=True, upper=-1)
    B.eStructuralFeatures.append(inner_ref)
    NamedElement.eStructuralFeatures.append(EReference('parent', eType=B, eOpposite=inner_ref))

    sibiling_ref = EReference('sibiling', eType=B)
    A.eStructuralFeatures.append(sibiling_ref)
    B.eStructuralFeatures.append(EReference('sibiling', eType=A, eOpposite=sibiling_ref))
    lib = EPackage('lib')
    lib.eClassifiers.extend([Root, NamedElement, A, B])
    lib.Root = Root
    lib.NamedElement = NamedElement
    lib.A = A
    lib.B = B
    return lib


def test_notification_dummy(lib):
    root = lib.Root()
    a1 = lib.A()
    observer = EObserver()
    observer.observe(root)
    root.namedElements.append(a1)


def test_notification_print(lib):
    root = lib.Root()
    a1 = lib.A()
    observer = EObserver()
    observer.observe(root)
    observer.notify = lambda x: x
    root.namedElements.append(a1)


def test_notification_add(lib):
    root = lib.Root()
    a1 = lib.A()
    notifyChanged = lambda x: assert_wrap(x.kind is Kind.ADD
                                          and x.new is a1
                                          and x.feature.name == 'namedElements'
                                          and x.notifier is root)
    observer = EObserver(root, notifyChanged=notifyChanged)
    root.namedElements.append(a1)


def test_notification_eopposite(lib):
    a1 = lib.A()
    b1 = lib.B()
    notify = lambda x: assert_wrap(x.kind is Kind.ADD
                                   and x.new is a1
                                   and x.feature.name == 'inner'
                                   and x.notifier is b1)
    o1 = EObserver(b1, notifyChanged=notify)
    notify = lambda x: assert_wrap(x.kind is Kind.SET
                                   and x.new is b1
                                   and x.feature.name == 'parent'
                                   and x.notifier is a1)
    o2 = EObserver(a1, notifyChanged=notify)


def test_notification_attribute(lib):
    a1 = lib.A()
    notify = lambda x: assert_wrap(x.kind is Kind.SET
                                   and x.old is None
                                   and x.new is 'test'
                                   and x.feature.name == 'name'
                                   and x.notifier is a1)
    o1 = EObserver(a1, notifyChanged=notify)
    a1.name = 'test'

    o1.notifyChanged = lambda x: assert_wrap(x.kind is Kind.SET
                                             and x.old is 'test'
                                             and x.new is 'test2'
                                             and x.feature.name == 'name'
                                             and x.notifier is a1)
    a1.name = 'test2'

    o1.notifyChanged = lambda x: assert_wrap(x.kind is Kind.UNSET
                                             and x.old is 'test2'
                                             and x.new is None
                                             and x.feature.name == 'name'
                                             and x.notifier is a1)
    a1.name = None


class ObserverCounter(EObserver):
    def __init__(self, notifier=None):
        super(ObserverCounter, self).__init__(notifier=notifier)
        self.calls = 0

    def notifyChanged(self, notification):
        self.repr = notification.__repr__()
        self.calls += 1
        self.kind = notification.kind
        self.value = notification.new

def test_notification_add_many(lib):
    root = lib.Root()
    a1 = lib.A()
    a2 = lib.A()
    o = ObserverCounter(root)
    root.namedElements.extend([a1, a2])
    assert o.calls == 1 and o.kind is Kind.ADD_MANY and a1 in o.value and a2 in o.value

    o.calls = 0
    root.ne_set.extend([a1, a2])
    assert o.calls == 1 and o.kind is Kind.ADD_MANY and a1 in o.value and a2 in o.value

    o.calls = 0
    root.ne_oset.extend([a1, a2])
    assert o.calls == 1 and o.kind is Kind.ADD_MANY and a1 in o.value and a2 in o.value
