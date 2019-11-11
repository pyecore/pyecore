from .ecore import EProxy, EObject
from .notification import Notification, Kind
from .ordered_set_patch import ordered_set
from collections.abc import MutableSet, MutableSequence


class BadValueError(TypeError):
    def __init__(self, got=None, expected=None, feature=None):
        if isinstance(expected, EProxy):
            expected.force_resolve()
            expected = expected._wrapped
        self.got = got
        self.expected = expected
        self.feature = feature
        msg = "Expected type {0}, but got type {1} with value {2} instead "
        msg = msg.format(expected, type(got).__name__, got)
        if feature:
            msg += "for feature {} of {}".format(feature,
                                                 feature.eContainingClass)
        super().__init__(msg)


class EcoreUtils(object):
    @staticmethod
    def isinstance(obj, _type):
        if obj is None:
            return True
        elif isinstance(obj, EProxy) and not obj.resolved:
            return True
        elif isinstance(obj, _type):
            return True
        try:
            return _type.__isinstance__(obj)
        except AttributeError:
            return False

    @staticmethod
    def get_root(obj):
        if not obj:
            return None
        previous = obj
        while previous.eContainer() is not None:
            previous = previous.eContainer()
        return previous


class PyEcoreValue(object):
    def __init__(self, owner, efeature):
        super().__init__()
        self.owner = owner
        self.feature = efeature
        self.is_ref = efeature and efeature.is_reference
        self.is_cont = self.is_ref and efeature.containment
        self.generic_type = None

    def check(self, value):
        etype = self.generic_type or self.feature.eType
        if not etype:
            try:
                etype = self.feature.eGenericType.eRawType
                self.generic_type = etype
            except Exception:
                raise AttributeError('Feature {} has no type'
                                     'nor generic'.format(self.feature))
        if not EcoreUtils.isinstance(value, etype):
            raise BadValueError(value, etype, self.feature)

    def _update_container(self, value, previous_value=None):
        if not self.is_cont:
            return
        if value:
            resource = value.eResource
            if resource and value in resource.contents:
                resource.remove(value)
            prev_container = value._container
            prev_feature = value._containment_feature
            if (prev_container != self.owner
                    or prev_feature != self.feature) \
                    and isinstance(prev_container, EObject):
                prev_container.__dict__[prev_feature.name] \
                              .remove_or_unset(value)
            value._container = self.owner
            value._containment_feature = self.feature
        if previous_value:
            previous_value._container = None
            previous_value._containment_feature = None


class EValue(PyEcoreValue):
    def __init__(self, owner, efeature):
        super().__init__(owner, efeature)
        self._value = efeature.get_default_value()

    def remove_or_unset(self, value, update_opposite=True):
        self._set(None, update_opposite)

    def _get(self):
        return self._value

    def _set(self, value, update_opposite=True):
        self.check(value)
        previous_value = self._value
        self._value = value
        owner = self.owner
        efeature = self.feature
        notif = Notification(old=previous_value,
                             new=value,
                             feature=efeature,
                             kind=Kind.UNSET if value is None else Kind.SET)
        owner.notify(notif)
        owner._isset.add(efeature)

        if not self.is_ref:
            return
        self._update_container(value, previous_value)
        if not update_opposite:
            return

        # if there is no opposite, we set inverse relation and return
        if not efeature.eOpposite:
            couple = (owner, efeature)
            if hasattr(value, '_inverse_rels'):
                if hasattr(previous_value, '_inverse_rels'):
                    previous_value._inverse_rels.remove(couple)
                value._inverse_rels.add(couple)
            elif value is None and hasattr(previous_value, '_inverse_rels'):
                previous_value._inverse_rels.remove(couple)
            return

        eOpposite = efeature.eOpposite
        # if we are in an 'unset' context
        opposite_name = eOpposite.name
        if value is None:
            if previous_value is None:
                return
            if eOpposite.many:
                object.__getattribute__(previous_value, opposite_name) \
                      .remove(owner, update_opposite=False)
            else:
                object.__setattr__(previous_value, opposite_name, None)
        else:
            previous_value = value.__getattribute__(opposite_name)
            if eOpposite.many:
                previous_value.append(owner, update_opposite=False)
            else:
                # We disable the eOpposite update
                value.__dict__[opposite_name]. \
                      _set(owner, update_opposite=False)


class ECollection(PyEcoreValue):
    @staticmethod
    def create(owner, feature):
        if feature.derived:
            return EDerivedCollection(owner, feature)
        elif feature.ordered and feature.unique:
            return EOrderedSet(owner, feature)
        elif feature.ordered and not feature.unique:
            return EList(owner, feature)
        elif feature.unique:
            return ESet(owner, feature)
        else:
            return EBag(owner, feature)  # see for better implem

    def __init__(self, owner, efeature):
        super().__init__(owner, efeature)

    def remove_or_unset(self, value, update_opposite=True):
        self.remove(value, update_opposite)

    def _get(self):
        return self

    def _update_opposite(self, owner, new_value, remove=False):
        eOpposite = self.feature.eOpposite
        if not eOpposite:
            couple = (new_value, self.feature)
            if remove and couple in owner._inverse_rels:
                owner._inverse_rels.remove(couple)
            else:
                owner._inverse_rels.add(couple)
            return

        opposite_name = eOpposite.name
        if eOpposite.many and not remove:
            owner.__getattribute__(opposite_name).append(new_value, False)
        elif eOpposite.many and remove:
            owner.__getattribute__(opposite_name).remove(new_value, False)
        else:
            new_value = None if remove else new_value
            owner.__getattribute__(opposite_name)  # Force load
            owner.__dict__[opposite_name] \
                 ._set(new_value, update_opposite=False)

    def remove(self, value, update_opposite=True):
        if self.is_ref:
            self._update_container(None, previous_value=value)
            if update_opposite:
                self._update_opposite(value, self.owner, remove=True)
        super().remove(value)
        self.owner.notify(Notification(old=value,
                                       feature=self.feature,
                                       kind=Kind.REMOVE))

    def insert(self, i, y):
        self.check(y)
        if self.is_ref:
            self._update_container(y)
            self._update_opposite(y, self.owner)
        super().insert(i, y)
        self.owner.notify(Notification(new=y,
                                       feature=self.feature,
                                       kind=Kind.ADD))
        self.owner._isset.add(self.feature)

    def pop(self, index=None):
        if index is None:
            value = super().pop()
        else:
            value = super().pop(index)
        if self.is_ref:
            self._update_container(None, previous_value=value)
            self._update_opposite(value, self.owner, remove=True)
        self.owner.notify(Notification(old=value,
                                       feature=self.feature,
                                       kind=Kind.REMOVE))
        return value

    def clear(self):
        for x in set(self):
            self.remove(x)

    def select(self, f):
        return [x for x in self if f(x)]

    def reject(self, f):
        return [x for x in self if not f(x)]

    def __iadd__(self, items):
        if ordered_set.is_iterable(items):
            self.extend(items)
        else:
            self.append(items)
        return self


class EList(ECollection, list):
    def __init__(self, owner, efeature=None):
        super().__init__(owner, efeature)

    def append(self, value, update_opposite=True):
        self.check(value)
        if self.is_ref:
            self._update_container(value)
            if update_opposite:
                self._update_opposite(value, self.owner)
        super().append(value)
        self.owner.notify(Notification(new=value,
                                       feature=self.feature,
                                       kind=Kind.ADD))
        self.owner._isset.add(self.feature)

    def extend(self, sublist):
        if self.is_ref:
            for value in sublist:
                self.check(value)
                self._update_container(value)
                self._update_opposite(value, self.owner)
        else:
            for value in sublist:
                self.check(value)

        super().extend(sublist)
        self.owner.notify(Notification(new=sublist,
                                       feature=self.feature,
                                       kind=Kind.ADD_MANY))
        self.owner._isset.add(self.feature)

    def __setitem__(self, i, y):
        is_collection = ordered_set.is_iterable(y)
        if isinstance(i, slice) and is_collection:
            sliced_elements = self.__getitem__(i)
            if self.is_ref:
                for element in y:
                    self.check(element)
                    self._update_container(element)
                    self._update_opposite(element, self.owner)
                # We remove (not really) all element from the slice
                for element in sliced_elements:
                    self._update_container(None, previous_value=element)
                    self._update_opposite(element, self.owner, remove=True)
            else:
                for element in y:
                    self.check(element)
            if sliced_elements and len(sliced_elements) > 1:
                self.owner.notify(Notification(old=sliced_elements,
                                               feature=self.feature,
                                               kind=Kind.REMOVE_MANY))
            elif sliced_elements:
                self.owner.notify(Notification(old=sliced_elements[0],
                                               feature=self.feature,
                                               kind=Kind.REMOVE))

        else:
            self.check(y)
            if self.is_ref:
                self._update_container(y)
                self._update_opposite(y, self.owner)
        super().__setitem__(i, y)
        kind = Kind.ADD
        if is_collection and len(y) > 1:
            kind = Kind.ADD_MANY
        elif is_collection:
            y = y[0] if y else y
        self.owner.notify(Notification(new=y,
                                       feature=self.feature,
                                       kind=kind))
        self.owner._isset.add(self.feature)


class EBag(EList):
    pass


class EAbstractSet(ECollection):
    def __init__(self, owner, efeature=None):
        super().__init__(owner, efeature)
        self._orderedset_update = False

    def append(self, value, update_opposite=True):
        self.add(value, update_opposite)

    def add(self, value, update_opposite=True):
        self.check(value)
        if self.is_ref:
            self._update_container(value)
            if update_opposite:
                self._update_opposite(value, self.owner)
        super().add(value)
        if not self._orderedset_update:
            self.owner.notify(Notification(new=value,
                                           feature=self.feature,
                                           kind=Kind.ADD))
        self.owner._isset.add(self.feature)

    def extend(self, sublist):
        self.update(sublist)

    # def update(self, others):
    #     if self.is_ref:
    #         for value in others:
    #             self.check(value)
    #             self._update_container(value)
    #             self._update_opposite(value, self.owner)
    #     else:
    #         for value in others:
    #             self.check(value)
    #     super().update(others)
    #     self.owner.notify(Notification(new=others,
    #                                    feature=self.feature,
    #                                    kind=Kind.ADD_MANY))
    #     self.owner._isset.add(self.feature)


class EOrderedSet(EAbstractSet, ordered_set.OrderedSet):
    def __init__(self, owner, efeature=None):
        super().__init__(owner, efeature)
        ordered_set.OrderedSet.__init__(self)

    def update(self, others):
        self._orderedset_update = True
        for value in others:
            super().add(value)
        self.owner.notify(Notification(new=others,
                                       feature=self.feature,
                                       kind=Kind.ADD_MANY))
        self._orderedset_update = False

    def copy(self):
        return ordered_set.OrderedSet(self)

    @staticmethod
    def subcopy(sublist):
        return ordered_set.OrderedSet(sublist)


class ESet(EOrderedSet):
    pass


class EDerivedCollection(MutableSet, MutableSequence, ECollection):
    @classmethod
    def create(cls, owner, feature=None):
        return cls(owner, feature)

    def __init__(self, owner, feature=None):
        super().__init__(owner, feature)

    def __delitem__(self, index):
        raise AttributeError('Operation not permited for "{}" feature'
                             .format(self.feature.name))

    def __getitem__(self, index):
        raise AttributeError('Operation not permited for "{}" feature'
                             .format(self.feature.name))

    def __len__(self):
        raise AttributeError('Operation not permited for "{}" feature'
                             .format(self.feature.name))

    def __setitem__(self, index, item):
        raise AttributeError('Operation not permited for "{}" feature'
                             .format(self.feature.name))

    def add(self, value):
        raise AttributeError('Operation not permited for "{}" feature'
                             .format(self.feature.name))

    def discard(self, value):
        raise AttributeError('Operation not permited for "{}" feature'
                             .format(self.feature.name))

    def insert(self, index, value):
        raise AttributeError('Operation not permited for "{}" feature'
                             .format(self.feature.name))
