import pytest
from pyecore.ecore import *


def test_default_derived_collection():
    collection = EDerivedCollection.create(None, None)
    assert len(collection) == 0

    with pytest.raises(AttributeError):
        collection[0]

    with pytest.raises(AttributeError):
        collection[0] = 4

    with pytest.raises(AttributeError):
        collection.insert(0, 4)

    with pytest.raises(AttributeError):
        collection.discard(4)

    with pytest.raises(AttributeError):
        del collection[0]

    with pytest.raises(AttributeError):
        collection.add(4)


def test_new_derived_collection():
    A = EClass('A')
    A.eStructuralFeatures.append(EAttribute('mod2', EInt, upper=-1))

    a = A()
    assert len(a.mod2) == 0


class DerivedMod2(EDerivedCollection):
    def _get_collection(self):
        return [x for x in self.owner.ages if x % 2 == 0]

    def __len__(self):
        return len(self._get_collection())

    def __getitem__(self, index):
        return self._get_collection()[index]


def test_new_factory_derived_collection():
    A = EClass('A')
    A.eStructuralFeatures.append(EAttribute('ages', EInt, upper=-1))
    A.eStructuralFeatures.append(EAttribute('mod2', EInt, upper=-1,
                                            derived_class=DerivedMod2))

    a = A()
    a.ages.extend([1, 2, 3, 4, 5, 6])
    assert isinstance(a.mod2, DerivedMod2)
    assert a.mod2
    assert len(a.mod2) == 3
    assert a.mod2[0] == 2
