""" This module introduce the command system which allows to defined various
that can be executed onto a commands stack. Each command can also be 'undo' and
'redo'.
"""
from abc import ABCMeta, abstractmethod
from collections import UserList
from .ecore import EObject, BadValueError
from .resources import ResourceSet


class Command(metaclass=ABCMeta):
    """Provides the basic elements that must be implemented by a custom command.
    The methods/properties that need to be implemented are:
    * can_execute (@property)
    * can_undo (@property)
    * execute (method)
    * undo (method)
    * redo (method)
    """
    @property
    @abstractmethod
    def can_execute(self):
        pass

    @abstractmethod
    def execute(self):
        pass

    @property
    @abstractmethod
    def can_undo(self):
        pass

    @abstractmethod
    def undo(self):
        pass

    @abstractmethod
    def redo(self):
        pass


class AbstractCommand(Command):
    def __init__(self, owner=None, feature=None, value=None, label=None):
        if owner and not isinstance(owner, EObject):
            raise BadValueError(got=owner, expected=EObject)
        self.owner = owner
        self.resource = owner.eResource
        self.feature = feature
        self.value = value
        self.previous_value = None
        self.label = label
        self._is_prepared = False
        self._is_executable = False

    @property
    def can_execute(self):
        execute = False
        eclass = self.owner.eClass
        if isinstance(self.feature, str):
            actual = eclass.findEStructuralFeature(self.feature)
            self.feature = actual
            execute = actual is not None
        else:
            actual = eclass.findEStructuralFeature(self.feature.name)
            execute = self.feature is actual
        return execute

    @property
    def can_undo(self):
        return self._executed

    def execute(self):
        self.do_execute()
        self._executed = True

    def __repr__(self):
        if self.feature is None:
            feature = 'NO_FEATURE'
        elif not isinstance(self.feature, str):
            feature = self.feature.name
        else:
            feature = self.feature
        return '{} {}.{} <- {}'.format(self.__class__.__name__,
                                       self.owner,
                                       feature,
                                       self.value)


class Set(AbstractCommand):
    def __init__(self, owner=None, feature=None, value=None):
        super().__init__(owner, feature, value)

    @property
    def can_execute(self):
        can = super().can_execute
        return can and not self.feature.many

    def undo(self):
        self.owner.eSet(self.feature, self.previous_value)

    def redo(self):
        self.owner.eSet(self.feature, self.value)

    def do_execute(self):
        object = self.owner
        self.previous_value = object.eGet(self.feature)
        object.eSet(self.feature, self.value)


class Add(AbstractCommand):
    def __init__(self, owner=None, feature=None, value=None, index=None):
        super().__init__(owner, feature, value)
        self.index = index
        self._collection = None

    @property
    def can_execute(self):
        executable = super().can_execute
        executable = executable and self.value is not None
        self._collection = self.owner.eGet(self.feature)
        return executable

    @property
    def can_undo(self):
        can = super().can_undo
        return can and self.value in self._collection

    def undo(self):
        self._collection.pop(self.index)

    def redo(self):
        self._collection.insert(self.index, self.value)

    def do_execute(self):
        if self.index is not None:
            self._collection.insert(self.index, self.value)
        else:
            self.index = len(self._collection)
            self._collection.append(self.value)


class Remove(AbstractCommand):
    def __init__(self, owner=None, feature=None, value=None, index=None):
        super().__init__(owner, feature, value)
        self.index = index
        self._collection = None
        if bool(self.index is not None) == bool(self.value is not None):
            raise ValueError('Remove command cannot have index and value set '
                             'together.')

    @property
    def can_execute(self):
        executable = super().can_execute
        self._collection = self.owner.eGet(self.feature)
        if self.index is None:
            executable = executable and self.value is not None
        else:
            self.value = self._collection[self.index]
        return executable

    def undo(self):
        self._collection.insert(self.index, self.value)

    def redo(self):
        self._collection.pop(self.index)

    def do_execute(self):
        if self.index is None:
            self.index = self._collection.index(self.value)
        self._collection.pop(self.index)


class Move(AbstractCommand):
    def __init__(self, owner=None, feature=None, from_index=None,
                 to_index=None, value=None):
        super().__init__(owner, feature, value=value)
        self.from_index = from_index
        self.to_index = to_index
        if bool(self.from_index is not None) == bool(self.value is not None):
            raise ValueError('Move command cannot have from_index and value '
                             'set together.')

    @property
    def can_execute(self):
        can = super().can_execute
        self._collection = self.owner.eGet(self.feature)
        if self.value is None:
            self.value = self._collection[self.from_index]
        if self.from_index is None:
            self.from_index = self._collection.index(self.value)
        return can and self.value in self._collection

    @property
    def can_undo(self):
        can = super().can_undo
        obj = self._collection[self.to_index]
        return can and obj is self.value

    def undo(self):
        self.value = self._collection.pop(self.to_index)
        self._collection.insert(self.from_index, self.value)

    def redo(self):
        self.do_execute()

    def do_execute(self):
        self.value = self._collection.pop(self.from_index)
        self._collection.insert(self.to_index, self.value)


class Delete(AbstractCommand):
    def __init__(self, owner=None):
        super().__init__(owner=owner)

    @property
    def can_execute(self):
        self.feature = self.owner.eContainmentFeature()
        self.references = {}
        elements = {self.owner}
        elements.update(self.owner.eAllContents())
        for element in elements:
            rels_tuple = [(ref, element.eGet(ref))
                          for ref in element.eClass.eAllReferences()]
            self.references[element] = rels_tuple
        self.inverse_references = {}
        for element in elements:
            rels_tuple = []
            for obj, reference in element._inverse_rels:
                if reference.many:
                    index = obj.eGet(reference).index(element)
                else:
                    index = 0
                rels_tuple.append((index, obj, reference))
            self.inverse_references[element] = rels_tuple
        return True

    def undo(self):
        for element, v in self.references.items():
            for reference, content in v:
                if reference.many:
                    element.eGet(reference).extend(content)
                else:
                    element.eSet(reference, content)
        for element, v in self.inverse_references.items():
            for i, obj, reference in v:
                if reference.many:
                    obj.eGet(reference).insert(i, element)
                else:
                    obj.eSet(reference, element)

    def redo(self):
        self.do_execute()

    def do_execute(self):
        self.owner.delete()

    def __repr__(self):
        return '{} {}'.format(self.__class__.__name__, self.owner)


class Compound(Command, UserList):
    def __init__(self, *commands):
        super().__init__(commands)

    @property
    def can_execute(self):
        return all(command.can_execute for command in self)

    def execute(self):
        for command in self:
            command.execute()

    @property
    def can_undo(self):
        return all(command.can_undo for command in self)

    def undo(self):
        for command in reversed(self):
            command.undo()

    def redo(self):
        for command in self:
            command.redo()

    def unwrap(self):
        return self[0] if len(self) == 1 else self

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.data)


class CommandStack(object):
    def __init__(self):
        self.stack = []
        self.stack_index = -1

    @property
    def top(self):
        return self.stack[self.stack_index]

    @property
    def peek_next_top(self):
        return self.stack[self.stack_index + 1]

    @top.setter
    def top(self, command):
        index = self.stack_index + 1
        self.stack[index:index] = [command]
        self.stack_index = index

    @top.deleter
    def top(self):
        self.stack_index -= 1

    def __bool__(self):
        return self.stack_index > -1

    def execute(self, *commands):
        for command in commands:
            if command.can_execute:
                command.execute()
                self.top = command
            else:
                raise ValueError('Cannot execute command {}'.format(command))

    def undo(self):
        if not self:
            raise IndexError('Command stack is empty')
        if self.top.can_undo:
            self.top.undo()
            del self.top

    def redo(self):
        self.peek_next_top.redo()
        self.stack_index += 1


class EditingDomain(object):
    def __init__(self, resource_set=None, command_stack_class=CommandStack):
        self.resource_set = resource_set or ResourceSet()
        self.__stack = command_stack_class()
        self.clipboard = []

    def create_resource(self, uri):
        return self.resource_set.create_resource(uri)

    def load_resource(self, uri):
        return self.resource_set.get_resource(uri)

    def execute(self, cmd):
        if cmd.resource not in self.resource_set.resources.values():
            raise ValueError("Cannot execute command '{}', the resource's "
                             "command is not contained in the editing domain "
                             "resource set.".format(cmd))
        self.__stack.execute(cmd)

    def undo(self):
        self.__stack.undo()

    def redo(self):
        self.__stack.redo()
