import pytest
import pyecore.ecore as Ecore
from pyecore.ecore import *
from pyecore.resources import global_registry, ResourceSet
from os import path


def teardown_module(module):
    global_registry.clear()
    global_registry[Ecore.nsURI] = Ecore


@pytest.fixture(scope='module')
def lib():
    package = EPackage('pack', nsURI='http://pack/1.0', nsPrefix='pack')
    A = EClass('A')
    B = EClass('B')
    Root = EClass('Root')
    Root.eStructuralFeatures.append(EReference('a', A, containment=True,
                                               upper=-1))
    Root.eStructuralFeatures.append(EReference('b', B, containment=True,
                                               upper=-1))

    A.eStructuralFeatures.append(EReference('tob', B, upper=-1,
                                            unique=False))
    A.eStructuralFeatures.append(EReference('containb', B, upper=1,
                                            containment=True))
    A.eStructuralFeatures.append(EReference('simpleb', B, upper=1))

    ref = EReference('invb', B, upper=1)
    A.eStructuralFeatures.append(ref)
    B.eStructuralFeatures.append(EReference('froma', A, upper=-1, eOpposite=ref))

    ref = EReference('multib', B, upper=-1)
    A.eStructuralFeatures.append(ref)
    B.eStructuralFeatures.append(EReference('sa', A, eOpposite=ref))
    package.eClassifiers.extend([Root, A, B])
    # we register the metamodel first
    global_registry[package.nsURI] = package
    return package


@pytest.fixture
def model2(lib):
    root = lib.getEClassifier('Root')()
    b = lib.getEClassifier('B')()
    root.b.append(b)
    return root


@pytest.fixture
def model1(lib, model2):
    root = lib.getEClassifier('Root')()
    a = lib.getEClassifier('A')()
    a.tob.append(model2.b[0])
    root.a.append(a)
    return root


def test_delete_simpledelete(model1):
    b = model1.a[0].tob[0]
    assert b.eContainer() is not None

    b.delete()
    assert len(model1.a[0].tob) == 0
    assert b.eContainer() is None
    assert b.eContainmentFeature() is None


def test_delete_simpledelete_newelement(model1, lib):
    a = model1.a[0]
    b = lib.getEClassifier('B')()
    a.containb = b
    assert b.eContainer() is not None

    b.delete()
    assert len(a.tob) == 1
    assert a.containb is None
    assert b.eContainer() is None
    assert b.eContainmentFeature() is None


def test_delete_deleteorder1(model1):
    a = model1.a[0]
    a.delete()
    assert len(model1.a) == 0
    assert a.eContainer() is None
    assert a.eContainmentFeature() is None


def test_delete_deleteorder2(model1, model2):
    a = model1.a[0]
    b = a.tob[0]
    a.delete()
    b.delete()
    assert len(model1.a) == 0
    assert a.eContainer() is None
    assert a.eContainmentFeature() is None
    assert len(model2.b) == 0
    assert b.eContainer() is None
    assert b.eContainmentFeature() is None


def test_delete_simpledelete_reccursive(model1, lib):
    a2 = lib.getEClassifier('A')()
    a = model1.a[0]
    b = lib.getEClassifier('B')()
    a.containb = b
    a2.tob.append(b)
    assert b.eContainer() is a

    a.delete()
    assert b not in a2.tob
    assert len(a2.tob) == 0


def test_delete_simpledelete_simple_relation_containment(model1, lib):
    a2 = lib.getEClassifier('A')()
    a = model1.a[0]
    b = lib.getEClassifier('B')()
    a.containb = b
    a2.tob.append(b)
    assert b.eContainer() is a

    b.delete()
    assert b.eContainer() is None
    assert a.containb is None
    assert len(a2.tob) == 0


def test_delete_simpledelete_simple_relation(model1, lib):
    a = model1.a[0]
    b = lib.getEClassifier('B')()
    a.simpleb = b
    assert a.simpleb is b

    b.delete()
    assert a.simpleb is None


def test_delete_simpledelete_simple_opposite(model1, lib):
    a = model1.a[0]
    b = lib.getEClassifier('B')()
    a.invb = b
    assert a.invb is b
    assert a in b.froma

    b.delete()
    assert a.simpleb is None
    assert len(b.froma) == 0


def test_delete_simpledelete_multi_opposite(model1, lib):
    a = model1.a[0]
    b = lib.getEClassifier('B')()
    a.multib.append(b)
    assert b in a.multib
    assert b.sa is a

    b.delete()
    assert len(a.multib) == 0
    assert b.sa is None


def test_delete_unresolved_proxy(lib):
    rset = ResourceSet()
    xmi_file = path.join('tests', 'xmi', 'xmi-tests', 'a1.xmi')
    root = rset.get_resource(xmi_file).contents[0]
    b = root.a[0].tob[0]
    b.delete()
    assert len(root.a[0].tob) == 0


def test_delete_unresolved_proxy_2_models_loaded(lib):
    rset = ResourceSet()
    xmi_file = path.join('tests', 'xmi', 'xmi-tests', 'a1.xmi')
    root = rset.get_resource(xmi_file).contents[0]

    xmi_file = path.join('tests', 'xmi', 'xmi-tests', 'b1.xmi')
    root2 = rset.get_resource(xmi_file).contents[0]
    b = root.a[0].tob[0]
    b.delete()
    assert len(root.a[0].tob) == 0
    assert len(root2.b) == 1  # the element is still here


def test_delete_resolved_proxy_2_models_loaded(lib):
    rset = ResourceSet()
    xmi_file = path.join('tests', 'xmi', 'xmi-tests', 'a1.xmi')
    root = rset.get_resource(xmi_file).contents[0]

    xmi_file = path.join('tests', 'xmi', 'xmi-tests', 'b1.xmi')
    root2 = rset.get_resource(xmi_file).contents[0]
    b = root.a[0].tob[0]
    b.force_resolve()
    b.delete()
    assert len(root.a[0].tob) == 0
    assert len(root2.b) == 0  # the element had been removed
    assert b.eContainer() is None


def test_delete_unresolved_proxy_loaded_models_from_pointed(lib):
    rset = ResourceSet()
    xmi_file = path.join('tests', 'xmi', 'xmi-tests', 'a1.xmi')
    root = rset.get_resource(xmi_file).contents[0]

    xmi_file = path.join('tests', 'xmi', 'xmi-tests', 'b1.xmi')
    root2 = rset.get_resource(xmi_file).contents[0]
    b = root2.b[0]
    b.delete()
    assert len(root.a[0].tob) == 1  # the element is still in the collection
    assert len(root2.b) == 0
    assert b.eContainer() is None


def test_delete_resolved_proxy_loaded_models_from_pointed(lib):
    rset = ResourceSet()
    xmi_file = path.join('tests', 'xmi', 'xmi-tests', 'a1.xmi')
    root = rset.get_resource(xmi_file).contents[0]

    xmi_file = path.join('tests', 'xmi', 'xmi-tests', 'b1.xmi')
    root2 = rset.get_resource(xmi_file).contents[0]
    root.a[0].tob[0].force_resolve()
    b = root2.b[0]
    b.delete()
    assert len(root.a[0].tob) == 0  # the element is not in the collection
    assert len(root2.b) == 0
    assert b.eContainer() is None


def test_delete_unresolved_proxy_simple_relation(lib):
    rset = ResourceSet()
    xmi_file = path.join('tests', 'xmi', 'xmi-tests', 'a3.xmi')
    root = rset.get_resource(xmi_file).contents[0]
    b = root.a[0].simpleb
    b.delete()
    assert len(root.a[0].tob) == 0


def test_delete_resolved_proxy_simple_relation(lib):
    rset = ResourceSet()
    xmi_file = path.join('tests', 'xmi', 'xmi-tests', 'b1.xmi')
    root2 = rset.get_resource(xmi_file).contents[0]

    xmi_file = path.join('tests', 'xmi', 'xmi-tests', 'a3.xmi')
    root = rset.get_resource(xmi_file).contents[0]
    b = root.a[0].simpleb
    b.force_resolve()
    b.delete()
    assert len(root.a[0].tob) == 0
    assert len(root2.b) == 0


def test_delete_unresolved_proxy_2_models_loaded_simple_relation(lib):
    rset = ResourceSet()
    xmi_file = path.join('tests', 'xmi', 'xmi-tests', 'a3.xmi')
    root = rset.get_resource(xmi_file).contents[0]

    xmi_file = path.join('tests', 'xmi', 'xmi-tests', 'b1.xmi')
    root2 = rset.get_resource(xmi_file).contents[0]
    b = root.a[0].simpleb
    b.delete()
    assert root.a[0].simpleb is None
    assert len(root2.b) == 1  # the element is still here


def test_delete_resolved_proxy_2_models_loaded_simple_relation(lib):
    rset = ResourceSet()
    xmi_file = path.join('tests', 'xmi', 'xmi-tests', 'a3.xmi')
    root = rset.get_resource(xmi_file).contents[0]

    xmi_file = path.join('tests', 'xmi', 'xmi-tests', 'b1.xmi')
    root2 = rset.get_resource(xmi_file).contents[0]
    b = root.a[0].simpleb
    b.force_resolve()
    b.delete()
    assert root.a[0].simpleb is None
    assert len(root2.b) == 0


def test_delete_unresolved_proxy_loaded_models_from_pointed_simple_rel(lib):
    rset = ResourceSet()
    xmi_file = path.join('tests', 'xmi', 'xmi-tests', 'a3.xmi')
    root = rset.get_resource(xmi_file).contents[0]

    xmi_file = path.join('tests', 'xmi', 'xmi-tests', 'b1.xmi')
    root2 = rset.get_resource(xmi_file).contents[0]
    b = root2.b[0]
    b.delete()
    assert root.a[0].simpleb is not None  # the element is still in the col.
    assert len(root2.b) == 0
    assert b.eContainer() is None


def test_delete_resolved_proxy_loaded_models_from_pointed_simple_rel(lib):
    rset = ResourceSet()
    xmi_file = path.join('tests', 'xmi', 'xmi-tests', 'a3.xmi')
    root = rset.get_resource(xmi_file).contents[0]

    xmi_file = path.join('tests', 'xmi', 'xmi-tests', 'b1.xmi')
    root2 = rset.get_resource(xmi_file).contents[0]
    root.a[0].simpleb.force_resolve()
    b = root2.b[0]
    b.delete()
    assert root.a[0].simpleb is None  # the element is still in the col.
    assert len(root2.b) == 0
    assert b.eContainer() is None


def test_delete_resolved_proxy_with_childre():
    A = Ecore.EClass('A')
    A.eStructuralFeatures.append(Ecore.EReference('children', A,
                                                  containment=True, upper=-1))
    a0, a1, a2, a3 = A(), A(), A(), A()
    a0.children.append(a1)
    a1.children.extend([a2, a3])

    proxy = Ecore.EProxy(wrapped=a1)
    proxy.delete()
    assert a0.children == []
