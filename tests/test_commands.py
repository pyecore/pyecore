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
    simple_tob = EReference('simple_tob', eType=B, containment=True)
    A.eStructuralFeatures.append(simple_tob)
    A.eStructuralFeatures.append(EReference('many_tob', eType=B,
                                            containment=True, upper=-1))
    B.eStructuralFeatures.append(EReference('toa', A))
    B.eStructuralFeatures.append(EReference('inverseA', A,
                                            eOpposite=simple_tob))
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

    a.many_tob.pop(-1)
    assert len(a.many_tob) == 0


def test_command_abs():
    class A(Command):
        def can_execute(self):
            super().can_execute

        def can_undo(self):
            super().can_undo

        def execute(self):
            super().execute()

        def undo(self):
            super().undo()

        def redo(self):
            super().redo()

    a = A()
    a.can_execute()
    a.execute()
    a.can_undo()
    a.undo()
    a.redo()


def test_command_set_name(mm):
    a = mm.A()

    with pytest.raises(BadValueError):
        Set(owner='R', feature='name', value='testValue')

    set = Set(owner=a, feature='name', value='testValue')
    assert set.__repr__()

    assert set.can_execute
    set.execute()
    assert a.name == 'testValue'
    assert set.can_undo
    set.undo()
    assert a.name is None
    set.redo()
    assert a.name == 'testValue'


def test_command_set_b(mm):
    a = mm.A()
    b = mm.B()

    set = Set(owner=a, feature='simple_tob', value=b)

    assert set.can_execute
    set.execute()
    assert a.simple_tob is b
    assert b.inverseA is a
    assert set.can_undo
    set.undo()
    assert a.simple_tob is None
    assert b.inverseA is None
    set.redo()
    assert a.simple_tob is b
    assert b.inverseA is a


def test_command_add_b(mm):
    a = mm.A()
    b = mm.B()

    add = Add(owner=a, feature='many_tob', value=b)

    assert add.can_execute
    add.execute()
    assert b in a.many_tob
    assert add.can_undo
    add.undo()
    assert b not in a.many_tob
    add.redo()
    assert b in a.many_tob


def test_command_add_b_index(mm):
    a = mm.A()
    b = mm.B()
    a.many_tob.append(b)

    b2 = mm.B()
    add = Add(owner=a, feature='many_tob', index=0, value=b2)

    assert add.can_execute
    add.execute()
    assert b2 in a.many_tob and b in a.many_tob
    assert a.many_tob.index(b2) == 0 and a.many_tob.index(b) == 1
    assert add.can_undo
    add.undo()
    assert b2 not in a.many_tob and b in a.many_tob
    assert a.many_tob.index(b) == 0
    add.redo()
    assert b2 in a.many_tob
    assert a.many_tob.index(b2) == 0 and a.many_tob.index(b) == 1


def test_command_set_name_stack(mm):
    root = mm.Root()
    a = mm.A()
    name_feature = mm.A.findEStructuralFeature('name')

    stack = CommandStack()
    set = Set(owner=a, feature=name_feature, value='testValue')
    assert set.__repr__()

    stack.execute(set)
    assert a.name == 'testValue'
    stack.undo()
    assert a.name is None
    stack.redo()
    assert a.name == 'testValue'
    assert set.__repr__()
