import pytest
from pyecore.ecore import *
from pyecore.utils import DynamicEPackage


@pytest.fixture(scope='module')
def simplemm():
    A = EClass('A')
    B = EClass('B')
    Root = EClass('Root')
    pack = EPackage('pack', nsURI='http://pack/1.0', nsPrefix='pack')
    pack.eClassifiers.extend([Root, A, B])
    return pack


@pytest.fixture(scope='module')
def complexmm():
    A = EClass('A')
    B = EClass('B')
    Root = EClass('Root')
    pack = EPackage('pack', nsURI='http://pack/1.0', nsPrefix='pack')
    pack.eClassifiers.extend([Root, A, B])

    innerpackage = EPackage('inner', nsURI='http://inner', nsPrefix='inner')
    C = EClass('C')
    D = EClass('D')
    innerpackage.eClassifiers.extend([C, D])
    pack.eSubpackages.append(innerpackage)
    return pack


def test_dynamic_access_eclasses(simplemm):
    SimpleMM = DynamicEPackage(simplemm)
    assert SimpleMM.A
    assert SimpleMM.B


def test_dynamic_access_innerpackage(complexmm):
    ComplexMM = DynamicEPackage(complexmm)
    assert ComplexMM.A
    assert ComplexMM.B
    assert ComplexMM.inner.C
    assert ComplexMM.inner.D


def test_dynamic_addition_eclasses(complexmm):
    ComplexMM = DynamicEPackage(complexmm)
    E = EClass('E')
    complexmm.eClassifiers.append(E)
    assert ComplexMM.E

    F = EClass('F')
    complexmm.eSubpackages[0].eClassifiers.append(F)
    assert ComplexMM.inner.F

    G = EClass('G')
    H = EClass('H')
    complexmm.eClassifiers.extend([G, H])
    assert ComplexMM.G
    assert ComplexMM.H


def test_dynamic_removal_eclasses(complexmm):
    ComplexMM = DynamicEPackage(complexmm)
    assert ComplexMM.Root

    complexmm.eClassifiers.remove(ComplexMM.Root)
    with pytest.raises(AttributeError):
        ComplexMM.Root

    assert ComplexMM.A
    complexmm.eClassifiers[0].delete()
    with pytest.raises(AttributeError):
        ComplexMM.A
