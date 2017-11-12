import pytest
import pyecore.ecore as Ecore
from pyecore.resources import ResourceSet
from pyecore.resources.json import JsonResource
from os import path


@pytest.fixture()
def rset():
    rset = ResourceSet()
    rset.resource_factory['json'] = lambda uri: JsonResource(uri)
    return rset


eClass = Ecore.EPackage(nsURI='http://test/1.0', name='pack', nsPrefix='pack')


@Ecore.EMetaclass
class A(object):
    name = Ecore.EAttribute(eType=Ecore.EString)
    children = Ecore.EReference(upper=-1, containment=True)
    parent = Ecore.EReference(eOpposite=children)

    def __init__(self, name=None, children=None):
        if children:
            self.children.update(children)
        self.name = name

    def __repr__(self):
        return self.name


A.children.eType = A
A.parent.eType = A


@pytest.fixture(scope='module')
def mm():
    return eClass


def test__jsonresource_factory_registration():
    rset = ResourceSet()
    rset.resource_factory['json'] = lambda uri: JsonResource(uri)
    resource = rset.create_resource('non_existing.json')
    assert isinstance(resource, JsonResource)

    # ensure that resource factory are not shared between resources sets
    rset = ResourceSet()
    resource = rset.create_resource('non_existing.json')
    assert not isinstance(resource, JsonResource)


def test__jsonresource_load_simple_ecore(rset):
    json_file = path.join('tests', 'json', 'data', 'simple.json')
    resource = rset.get_resource(json_file)
    root = resource.contents[0]
    assert isinstance(root, Ecore.EPackage)


def test__jsonresource_load_simple_ecore(rset):
    json_file = path.join('tests', 'json', 'data', 'simple.json')
    resource = rset.get_resource(json_file)
    root = resource.contents[0]
    assert isinstance(root, Ecore.EPackage)
    assert root.name == 'pack'


def test__jsonresource_load_crossref_ecore(rset):
    json_file = path.join('tests', 'json', 'data', 'f2.json')
    resource = rset.get_resource(json_file)
    root = resource.contents[0]
    assert isinstance(root, Ecore.EPackage)

    json_file = path.join('tests', 'json', 'data', 'f1.json')
    resource = rset.get_resource(json_file)
    root = resource.contents[0]
    assert isinstance(root, Ecore.EPackage)
    assert isinstance(root.eClassifiers[0].eStructuralFeatures[0].eType,
                      Ecore.EProxy)
    assert root.eClassifiers[0].eStructuralFeatures[0].eType.name == 'B'
    assert isinstance(root.eClassifiers[0].eStructuralFeatures[1].eType,
                      Ecore.EProxy)
    # auto-load kicks in
    assert root.eClassifiers[0].eStructuralFeatures[1].eType.name == 'C'

    # we load it, we have the same result
    json_file = path.join('tests', 'json', 'data', 'relative', 'f2.json')
    rset.get_resource(json_file)
    assert root.eClassifiers[0].eStructuralFeatures[1].eType.name == 'C'


def test__jsonresource_load_mm_instance(rset, mm):
    rset.metamodel_registry[mm.nsURI] = mm

    json_file = path.join('tests', 'json', 'data', 'd1.json')
    resource = rset.get_resource(json_file)
    root = resource.contents[0]
    assert isinstance(root, A)
    assert root.name == 'a1'
    assert root.children

    a2, a3 = root.children
    assert a2.parent is root and a2.name == 'a2'
    assert a3.parent is root and a3.name == 'a3'

    a4 = a2.children[0]
    assert a4.parent is a2 and a4.name == 'a4'


def test__jsonresource_load_mm_errors(rset, mm):
    rset.metamodel_registry[mm.nsURI] = mm

    json_file = path.join('tests', 'json', 'data', 'e1.json')
    with pytest.raises(ValueError):
        rset.get_resource(json_file)

    json_file = path.join('tests', 'json', 'data', 'e2.json')
    with pytest.raises(ValueError):
        rset.get_resource(json_file)


def test__jsonresource_load_enum_incomplete_eclassrefs(rset):
    mm_file = path.join('tests', 'json', 'data', 'minimal.ecore')
    mm = rset.get_resource(mm_file).contents[0]
    rset.metamodel_registry[mm.nsURI] = mm

    A = mm.getEClassifier('A')
    B = mm.getEClassifier('B')
    C = mm.getEClassifier('C')

    MyEnum = mm.getEClassifier('MyEnum')

    json_file = path.join('tests', 'json', 'data', 'minimal.json')
    root = rset.get_resource(json_file).contents[0]

    assert len(root.aContainer) == 1
    assert len(root.bContainer) == 2
    assert root.aContainer[0].eClass is A
    assert root.bContainer[0].eClass is B
    assert root.bContainer[1].eClass is C
    assert root.bContainer[0].enumatt is MyEnum.getEEnumLiteral('ABC')
    assert root.bContainer[1].enumatt is MyEnum.getEEnumLiteral('DEF')
