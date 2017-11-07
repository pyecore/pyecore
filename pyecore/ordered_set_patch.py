import ordered_set


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
                       'for {}'.format(self.__class__.__name__))
    if index < 0:
        index = len(self.items) + index
        if index < 0:
            raise IndexError('assignement index out of range')
    self.pop(index)
    self.insert(index, item)


ordered_set.OrderedSet.insert = insert
ordered_set.OrderedSet.pop = pop
ordered_set.OrderedSet.__setitem__ = __setitem__
