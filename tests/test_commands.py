import pytest
from pyecore.ecore import *
from pyecore.commands import *
from pyecore.utils import DynamicEPackage
from pyecore.notification import EObserver, Kind


class LastObserver(EObserver):
    def __init__(self, notifier=None):
        super().__init__(notifier=notifier)
        self.last = None

    def notifyChanged(self, notification):
        self.last = notification


@pytest.fixture(scope='module')
def mm():
    Root = EClass('Root')
    A = EClass('A')
    B = EClass('B')
    Root.eStructuralFeatures.append(EReference('as', A, upper=-1,
                                               containment=True))
    Root.eStructuralFeatures.append(EReference('bs', B, upper=-1,
                                               containment=True))
    A.eStructuralFeatures.append(EAttribute('name', EString))
    A.eStructuralFeatures.append(EReference('simple_tob', eType=B,
                                            containment=True))
    A.eStructuralFeatures.append(EReference('many_tob', eType=B,
                                            containment=True, upper=-1))
    B.eStructuralFeatures.append(EReference('toa', A))
    package = EPackage(name='package')
    package.eClassifiers.extend([Root, A, B])
    return DynamicEPackage(package)


def test_orderedset_insert(mm):
    a = mm.A()
    b = mm.B()
    a.many_tob.insert(0, b)
    assert b in a.many_tob
    assert a.many_tob.index(b) == 0
    a.many_tob.insert(0, b)
    assert b in a.many_tob

    b2 = mm.B()
    a.many_tob.insert(0, b2)
    assert b2 in a.many_tob
    assert a.many_tob.index(b) == 1
    assert a.many_tob.index(b2) == 0


def test_orderedset_pop(mm):
    a = mm.A()
    with pytest.raises(KeyError):
        a.many_tob.pop()
    with pytest.raises(KeyError):
        a.many_tob.pop(0)

    # add/remove one element
    b = mm.B()
    a.many_tob.append(b)
    assert b in a.many_tob
    a.many_tob.pop()
    assert len(a.many_tob) == 0

    b2 = mm.B()
    a.many_tob.extend([b, b2])
    assert b in a.many_tob and b2 in a.many_tob
    a.many_tob.pop()
    assert b in a.many_tob and b2 not in a.many_tob
    assert a.many_tob.index(b) == 0

    a.many_tob.append(b2)
    a.many_tob.pop(0)
    assert b not in a.many_tob and b2 in a.many_tob
    assert a.many_tob.index(b2) == 0


def test_command_set_name(mm):
    root = mm.Root()
    a = mm.A()

    stack = CommandStack()
    set = Set(owner=a, feature='name', value='testValue')
    stack.execute(set)
    assert a.name == 'testValue'
    stack.undo()
    assert a.name is None
    stack.redo()
    assert a.name == 'testValue'
