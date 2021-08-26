# -*- coding: future_fstrings -*-
import ordered_set
from typing import Iterable


SLICE_ALL = ordered_set.SLICE_ALL


# monkey patching the OrderedSet implementation
def insert(self, index, key):
    """Adds an element at a dedicated position in an OrderedSet.

    This implementation is meant for the OrderedSet from the ordered_set
    package only.
    """
    if key in self.map:
        return
    # compute the right index
    size = len(self.items)
    if index < 0:
        index = size + index if size + index > 0 else 0
    else:
        index = index if index < size else size
    # insert the value
    self.items.insert(index, key)
    for k, v in self.map.items():
        if v >= index:
            self.map[k] = v + 1
    self.map[key] = index


def pop(self, index=None):
    """Removes an element at the tail of the OrderedSet or at a dedicated
    position.

    This implementation is meant for the OrderedSet from the ordered_set
    package only.
    """
    if not self.items:
        raise KeyError('Set is empty')

    def remove_index(i):
        elem = self.items[i]
        del self.items[i]
        del self.map[elem]
        return elem
    if index is None:
        elem = remove_index(-1)
    else:
        size = len(self.items)
        if index < 0:
            index = size + index
            if index < 0:
                raise IndexError('assignement index out of range')
        elif index >= size:
            raise IndexError('assignement index out of range')
        elem = remove_index(index)
        for k, v in self.map.items():
            if v >= index and v > 0:
                self.map[k] = v - 1
    return elem


def __setitem__(self, index, item):
    if isinstance(index, slice):
        raise KeyError('Item assignation using slices is not yet supported '
                       f'for {self.__class__.__name__}')
    if index < 0:
        index = len(self.items) + index
        if index < 0:
            raise IndexError('assignement index out of range')
    self.pop(index)
    self.insert(index, item)


def __getitem__(self, index):
    if isinstance(index, slice) and index == SLICE_ALL:
        return self.copy()
    elif isinstance(index, Iterable):
        return self.subcopy(self.items[i] for i in index)
    elif isinstance(index, slice) or hasattr(index, "__index__"):
        result = self.items[index]
        if isinstance(result, list):
            return self.subcopy(result)
        else:
            return result
    else:
        raise TypeError("Don't know how to index an OrderedSet by %r" % index)


def subcopy(self, subitems):
    """
    This method is here mainly for overriding
    """
    return self.__class__(subitems)


ordered_set.OrderedSet.insert = insert
ordered_set.OrderedSet.pop = pop
ordered_set.OrderedSet.__setitem__ = __setitem__
ordered_set.OrderedSet.__getitem__ = __getitem__
ordered_set.OrderedSet.subcopy = subcopy
