import pytest
from pyecore.ecore import *
from pyecore.commands import *
from pyecore.resources import URI, ResourceSet
from pyecore.utils import DynamicEPackage
from pyecore.notification import EObserver, Kind
from os import path


class LastObserver(EObserver):
    def __init__(self, notifier=None):
        super(LastObserver, self).__init__(notifier=notifier)
        self.last = None

    def notifyChanged(self, notification):
        self.last = notification


@pytest.fixture(scope='module')
def mm():
    Root = EClass('Root')
    A = EClass('A')
    B = EClass('B')
    Root.eStructuralFeatures.append(EReference('a_s', A, upper=-1,
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
            super(A, self).can_execute

        def can_undo(self):
            super(A, self).can_undo

        def execute(self):
            super(A, self).execute()

        def undo(self):
            super(A, self).undo()

        def redo(self):
            super(A, self).redo()

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


def test_command_remove_b(mm):
    a = mm.A()
    b = mm.B()
    b2 = mm.B()

    a.many_tob.extend([b, b2])

    remove = Remove(owner=a, feature='many_tob', value=b)

    assert remove.can_execute
    remove.execute()
    assert b2 in a.many_tob and b not in a.many_tob
    assert a.many_tob.index(b2) == 0
    assert remove.can_undo
    remove.undo()
    assert b2 in a.many_tob and b in a.many_tob
    assert a.many_tob.index(b) == 0 and a.many_tob.index(b2)
    remove.redo()
    assert b2 in a.many_tob and b not in a.many_tob
    assert a.many_tob.index(b2) == 0


def test_command_remove_index(mm):
    a = mm.A()
    b = mm.B()
    b2 = mm.B()

    with pytest.raises(ValueError):
        Remove(owner=a, feature='many_tob', index=0, value=b)

    a.many_tob.extend([b, b2])

    remove = Remove(owner=a, feature='many_tob', index=0)

    assert remove.can_execute
    remove.execute()
    assert b2 in a.many_tob and b not in a.many_tob
    assert a.many_tob.index(b2) == 0
    assert remove.can_undo
    remove.undo()
    assert b2 in a.many_tob and b in a.many_tob
    assert a.many_tob.index(b) == 0 and a.many_tob.index(b2)
    remove.redo()
    assert b2 in a.many_tob and b not in a.many_tob
    assert a.many_tob.index(b2) == 0


def test_command_move_fromindex(mm):
    a = mm.A()
    b = mm.B()
    b2 = mm.B()
    a.many_tob.extend([b, b2])

    with pytest.raises(ValueError):
        Move(owner=a, feature='many_tob', from_index=0, value=b)

    assert a.many_tob.index(b) == 0 and a.many_tob.index(b2) == 1

    move = Move(owner=a, feature='many_tob', from_index=0, to_index=1)
    assert move.can_execute
    move.execute()
    assert a.many_tob.index(b) == 1 and a.many_tob.index(b2) == 0

    assert move.can_undo
    move.undo()
    assert a.many_tob.index(b) == 0 and a.many_tob.index(b2) == 1

    move.redo()
    assert a.many_tob.index(b) == 1 and a.many_tob.index(b2) == 0


def test_command_move_b(mm):
    a = mm.A()
    b = mm.B()
    b2 = mm.B()
    a.many_tob.extend([b, b2])

    assert a.many_tob.index(b) == 0 and a.many_tob.index(b2) == 1

    move = Move(owner=a, feature='many_tob', to_index=1, value=b)
    assert move.can_execute
    move.execute()
    assert a.many_tob.index(b) == 1 and a.many_tob.index(b2) == 0

    assert move.can_undo
    move.undo()
    assert a.many_tob.index(b) == 0 and a.many_tob.index(b2) == 1

    move.redo()
    assert a.many_tob.index(b) == 1 and a.many_tob.index(b2) == 0


def test_command_delete_b(mm):
    a = mm.A()
    b = mm.B()
    b2 = mm.B()
    a.many_tob.extend([b, b2])
    b.toa = a

    delete = Delete(owner=b)
    assert delete.can_execute
    delete.execute()
    assert b not in a.many_tob
    assert b.toa is None

    assert delete.can_undo
    delete.undo()
    assert b in a.many_tob
    assert b.toa is a

    delete.redo()
    assert b not in a.many_tob
    assert b.toa is None


def test_command_delete_graph(mm):
    root = mm.Root()
    a = mm.A()
    b = mm.B()
    b2 = mm.B()
    a.many_tob.extend([b, b2])
    b.toa = a
    root.a_s.append(a)

    delete = Delete(owner=a)
    assert delete.can_execute
    delete.execute()
    assert a not in root.a_s
    assert b not in a.many_tob
    assert b2 not in a.many_tob
    assert b.toa is None

    assert delete.can_undo
    delete.undo()
    assert a in root.a_s
    assert b in a.many_tob
    assert b2 in a.many_tob
    assert b.toa is a

    delete.redo()
    assert a not in root.a_s
    assert b not in a.many_tob
    assert b2 not in a.many_tob
    assert b.toa is None


def test_command_delete_inverse(mm):
    root = mm.Root()
    a = mm.A()
    b = mm.B()
    b.toa = a

    delete = Delete(owner=a)
    assert delete.can_execute
    delete.execute()
    assert b.toa is None

    assert delete.can_undo
    delete.undo()
    assert b.toa is a

    delete.redo()
    assert b.toa is None


def test_command_compound_basics(mm):
    a = mm.A()
    b = mm.B()
    b.toa = a

    set = Set(owner=a, feature='name', value='testValue')
    delete = Delete(owner=a)
    compound = Compound(set, delete)
    assert len(compound) == 2
    assert compound[0] is set
    assert compound[1] is delete
    assert compound.__repr__()

    del compound[0]
    assert len(compound) == 1
    assert compound[0] is delete
    compound.insert(0, set)
    for i, c in enumerate(compound):
        if i == 0:
            assert isinstance(c, Set)
        else:
            assert isinstance(c, Delete)
    del compound[0]
    assert len(compound) == 1
    compound[0:0] = [set]
    assert len(compound) == 2
    assert compound[0] is set


def test_command_compound_exec(mm):
    a = mm.A()

    set = Set(owner=a, feature='name', value='testValue')
    compound = Compound(set,
                        Set(owner=a, feature='name', value='testValue2'))
    assert compound.can_execute
    compound.execute()
    assert a.name == 'testValue2'

    assert compound.can_undo
    compound.undo()
    assert a.name is None

    compound.redo()
    assert a.name == 'testValue2'

    assert compound is compound.unwrap()
    del compound[1]
    assert set is compound.unwrap()


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


def test_stack_simple(mm):
    stack = CommandStack()
    with pytest.raises(IndexError):
        stack.undo()

    a = mm.A()
    with pytest.raises(ValueError):
        stack.execute(Set(a, 'names', 'test'))

    stack.execute(Set(a, 'name', 'testValue'))
    stack.execute(Set(a, 'name', 'testValue2'))
    assert a.name == 'testValue2'
    stack.undo()
    assert a.name == 'testValue'
    stack.undo()
    assert a.name is None


def test_stack_complex(mm):
    stack = CommandStack()
    a = mm.A()
    b1 = mm.B()
    b2 = mm.B()

    stack.execute(Set(a, 'name', 'testValue'))
    stack.execute(Add(a, 'many_tob', b1))
    stack.execute(Add(a, 'many_tob', b2))
    stack.execute(Set(b1, 'toa', a))
    stack.execute(Delete(b1))
    stack.execute(Set(a, 'name', 'final'))
    assert a.name == 'final'
    assert b2 in a.many_tob and b1 not in a.many_tob

    stack.undo()
    assert a.name == 'testValue'
    stack.undo()
    assert b1 in a.many_tob
    assert b1.toa is a

    stack.undo()
    assert b1.toa is None

    stack.undo()
    stack.undo()
    assert len(a.many_tob) == 0
    stack.undo()
    assert a.name is None

    with pytest.raises(IndexError):
        stack.undo()


def test_stack_multiple_undo_redo(mm):
    stack = CommandStack()
    a = mm.A()
    b1 = mm.B()

    stack.execute(Set(a, 'name', 'testValue'))
    stack.execute(Add(a, 'many_tob', b1))
    assert a.name == 'testValue'
    assert b1 in a.many_tob

    stack.undo()
    stack.undo()
    assert a.name is None
    assert b1 not in a.many_tob

    stack.redo()
    stack.redo()
    assert a.name == 'testValue'
    assert b1 in a.many_tob


def test_command_resource(mm):
    rset = ResourceSet()
    resource = rset.create_resource(URI('http://logical'))
    a = mm.A()
    resource.append(a)
    cmd = Set(a, 'name', 'test_value')
    assert cmd.resource is resource
