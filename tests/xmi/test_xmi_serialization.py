import pytest
import os
from lxml import etree
import pyecore.ecore as Ecore
from pyecore.resources import *
from pyecore.resources.xmi import XMIResource, XMIOptions, XMI_URL
from pyecore.utils import DynamicEPackage


@pytest.fixture(scope='module')
def lib():
    package = Ecore.EPackage('mypackage')
    package.nsURI = 'http://simplemetamodel/1.0'
    package.nsPrefix = 'simplemm'
    AbsA = Ecore.EClass('AbsA', abstract=True)
    AbsA.eStructuralFeatures.append(Ecore.EReference('toa', AbsA))
    A = Ecore.EClass('A', superclass=(AbsA,))
    SubA = Ecore.EClass('SubA', superclass=(A,))
    MyRoot = Ecore.EClass('MyRoot')
    MyRoot.a_container = Ecore.EReference('a_container', eType=AbsA, upper=-1,
                                          containment=True)
    MyRoot.eStructuralFeatures.append(MyRoot.a_container)
    package.eClassifiers.extend([MyRoot, A, SubA, AbsA])
    package.MyRoot = MyRoot
    package.SubA = SubA
    package.A = A
    # we register the metamodel first
    global_registry[package.nsURI] = package
    return package


def test_resource_createset(tmpdir, lib):
    f = tmpdir.mkdir('pyecore-tmp').join('test.xmi')
    resource = XMIResource(URI(str(f)))

    # we create some instances
    root = lib.MyRoot()
    a1 = lib.A()
    suba1 = lib.SubA()
    root.a_container.extend([a1, suba1])

    # we add the elements to the resource
    resource.append(root)
    resource.save()

    # we read the model
    resource = XMIResource(URI(str(f)))
    resource.load()
    assert resource.contents != []
    assert len(resource.contents[0].eContents) == 2


def test_resource_createSaveModifyRead(tmpdir, lib):
    f = tmpdir.mkdir('pyecore-tmp').join('test.xmi')
    resource = XMIResource(URI(str(f)))

    # we create some instances
    root = lib.MyRoot()
    a1 = lib.A()
    suba1 = lib.SubA()
    root.a_container.extend([a1, suba1])

    # we add the elements to the resource
    resource.append(root)
    resource.save()

    # we add more instances
    a2 = lib.A()
    root.a_container.append(a2)

    # we save again
    resource.save()

    # we read the model
    resource = XMIResource(URI(str(f)))
    resource.load()
    assert resource.contents != []
    assert len(resource.contents[0].eContents) == 3


eClass = Ecore.EPackage(name='test', nsURI='http://test/1.0',
                        nsPrefix='test')


@Ecore.EMetaclass
class A(object):
    name = Ecore.EAttribute('name', Ecore.EString)
    age = Ecore.EAttribute('age', Ecore.EInt)
    names = Ecore.EAttribute(eType=Ecore.EString, upper=-1)


def test_xmi_ecore_save_load(tmpdir):
    f = tmpdir.mkdir('pyecore-tmp').join('test.xmi')
    resource = XMIResource(URI(str(f)))

    resource.append(eClass)
    resource.save()

    resource = XMIResource(URI(str(f)))
    resource.load()
    root = resource.contents[0]
    assert root.name == 'test'
    assert root.getEClassifier('A') is not None


def test_xmi_ecore_save_option_xmitype(tmpdir):
    f = tmpdir.mkdir('pyecore-tmp').join('xmitype.xmi')
    resource = XMIResource(URI(str(f)))

    resource.append(eClass)
    resource.save(options={XMIOptions.OPTION_USE_XMI_TYPE: True})

    has_xmi_type = False
    with open(str(f)) as output:
        for line in output:
            if 'xmi:type="' in line:
                has_xmi_type = True
                break
    assert has_xmi_type

    resource.save()
    has_xmi_type = False
    with open(str(f)) as output:
        for line in output:
            if 'xmi:type="' in line:
                has_xmi_type = True
                break
    assert has_xmi_type is False


def test_xmi_ecore_save_heterogeneous_metamodel(tmpdir):
    f = tmpdir.mkdir('pyecore-tmp').join('heterogeneous.xmi')

    # Build a simple metamodel
    Root = Ecore.EClass('Root')
    Root.eStructuralFeatures.append(Ecore.EReference('element', Ecore.EObject))
    pack = Ecore.EPackage('mypack', nsURI='http://mypack/1.0',
                          nsPrefix='mypack_pref')
    pack.eClassifiers.append(Root)

    rset = ResourceSet()

    resource = rset.get_resource('tests/xmi/xmi-tests/My.ecore')
    root = resource.contents[0]
    rset.metamodel_registry[root.nsURI] = root

    # We open a first model with a special metamodel
    resource = rset.get_resource('tests/xmi/xmi-tests/MyRoot.xmi')
    root1 = resource.contents[0]

    r = Root(element=root1)
    resource = rset.create_resource(URI(str(f)))
    resource.append(r)
    resource.save()

    with open(str(f), 'r') as f:
        tree = etree.parse(f)
        xmlroot = tree.getroot()
        assert 'mypack_pref' in xmlroot.nsmap
        assert 'myprefix' in xmlroot.nsmap


def test_xmi_save_none_value(tmpdir):
    f = tmpdir.mkdir('pyecore-tmp').join('default_none_value.xmi')

    # Build a simple metamodel
    Root = Ecore.EClass('Root')
    Root.eStructuralFeatures.append(Ecore.EReference('element', Ecore.EObject))
    Root.eStructuralFeatures.append(Ecore.EAttribute('name', Ecore.EString))
    Root.eStructuralFeatures.append(Ecore.EAttribute('ints', Ecore.EInt,
                                                     upper=-1))
    pack = Ecore.EPackage('mypack', nsURI='http://mypack/1.0',
                          nsPrefix='mypack_pref')
    pack.eClassifiers.append(Root)

    r = Root()
    r.element = None
    r.name = None
    r.ints.extend([3, 4, 5])

    rset = ResourceSet()
    resource = rset.create_resource(URI(str(f)))
    resource.append(r)
    resource.save(options={XMIOptions.SERIALIZE_DEFAULT_VALUES: True})

    with open(str(f), 'r') as f:
        tree = etree.parse(f)
        xmlroot = tree.getroot()
        assert xmlroot[0].tag in ('name', 'element')
        assert xmlroot[1].tag in ('name', 'element')
        assert xmlroot[0].tag != xmlroot[1].tag


def test_xmi_save_empty_model(tmpdir):
    f = tmpdir.mkdir('pyecore-tmp').join('empty.xmi')

    rset = ResourceSet()
    resource = rset.create_resource(URI(str(f)))
    resource.save()


def test_xmi_multiroot_save(tmpdir):
    # Define a simple model that will be split in many roots
    A = Ecore.EClass('A')
    A.eStructuralFeatures.append(Ecore.EAttribute('name', Ecore.EString))
    pack1 = Ecore.EPackage('pack1', nsURI='http://pack1/1.0', nsPrefix='pack1')
    pack1.eClassifiers.append(A)

    B = Ecore.EClass('B')
    B.eStructuralFeatures.append(Ecore.EAttribute('age', Ecore.EInt))
    B.eStructuralFeatures.append(Ecore.EReference('to_a', A))
    pack2 = Ecore.EPackage('pack2', nsURI='http://pack2/1.0', nsPrefix='pack2')
    pack2.eClassifiers.append(B)

    f = tmpdir.mkdir('pyecore-tmp').join('multi_root.xmi')
    rset = ResourceSet()
    resource = rset.create_resource(URI(str(f)))
    resource.append(pack1)
    resource.append(pack2)
    resource.save()

    with open(str(f), 'r') as f:
        tree = etree.parse(f)
        xmlroot = tree.getroot()
        assert xmlroot.tag == '{{{0}}}XMI'.format(XMI_URL)


def test_resource_crossref_uuid(tmpdir, lib):
    f1 = tmpdir.mkdir('pyecore-tmp2').join('main_uuid1.xmi')
    f2 = tmpdir.join('pyecore-tmp2', 'href_uuid2.xmi')
    r1 = XMIResource(URI(str(f1)))
    r2 = XMIResource(URI(str(f2)))
    r2.use_uuid = True

    # we create some instances
    root = lib.MyRoot()
    a1 = lib.A()
    a2 = lib.SubA()
    a1.toa = a2
    root.a_container.append(a1)

    # we add the elements to the first resource
    r1.append(root)

    # we create and add element to the second resource
    root2 = lib.MyRoot()
    root2.a_container.append(a2)
    r2.append(root2)

    r1.save()
    r2.save()

    # we read the model
    rset = ResourceSet()
    resource = rset.get_resource(URI(str(f1)))
    resource.load()
    assert resource.contents != []
    assert len(resource.contents[0].eContents) == 1
    a_obj = resource.contents[0].eContents[0]
    a_obj.toa.force_resolve()
    assert isinstance(a_obj.toa, lib.SubA)


def test_xmi_save_load_EDate(tmpdir):
    from datetime import datetime
    f = tmpdir.mkdir('pyecore-tmp').join('default_date.xmi')

    # Build a simple metamodel
    Root = Ecore.EClass('Root')
    Root.eStructuralFeatures.append(Ecore.EAttribute('date', Ecore.EDate))
    pack = Ecore.EPackage('mypack', nsURI='http://mypack/1.0',
                          nsPrefix='mypack_pref')
    pack.eClassifiers.append(Root)

    date = datetime.utcnow()
    r = Root()
    r.date = date

    rset = ResourceSet()
    resource = rset.create_resource(URI(str(f)))
    resource.append(r)
    resource.save()

    rset = ResourceSet()
    rset.metamodel_registry[pack.nsURI] = pack
    resource = rset.get_resource(URI(str(f)))
    assert resource.contents[0].date == date


def test_xmi_many_string_serialization(tmpdir):
    rset = ResourceSet()
    rset.metamodel_registry[eClass.nsURI] = eClass

    f = tmpdir.mkdir('pyecore-tmp').join('many_string_no_whitespace.xmi')
    a1 = A()
    a1.names.append('test1')
    a1.names.append('test2')
    a1.names.append('test3')
    resource = rset.create_resource(str(f))
    resource.append(a1)
    resource.save()
    rset.resources.clear()
    assert rset.resources == {}
    root = rset.get_resource(str(f)).contents[0]
    assert 'test1' == root.names[0]
    assert 'test2' == root.names[1]
    assert 'test3' == root.names[2]

    f = tmpdir.join('pyecore-tmp', 'many_string_whitespace.xmi')
    a1 = A()
    a1.names.append('test 1')
    a1.names.append('test 2')
    a1.names.append('test3"')
    a1.names.append('')
    a1.names.append('    ')
    resource = rset.create_resource(str(f))
    resource.append(a1)
    resource.save()
    rset.resources.clear()
    assert rset.resources == {}
    root = rset.get_resource(str(f)).contents[0]
    assert 'test 1' == root.names[0]
    assert 'test 2' == root.names[1]
    assert 'test3"' == root.names[2]
    assert '' == root.names[3]
    assert '    ' == root.names[4]



def test_xmi_save_urimapper(tmpdir):
    import pyecore.type as types
    rset = ResourceSet()
    rset.metamodel_registry[types.nsURI] = types

    uri_mapper = rset.uri_mapper
    uri_mapper['plateforme://eclipse.stuff'] = 'http://www.eclipse.org/emf/2002'
    uri_mapper['plateforme://test'] = os.path.join('..', 'xmi-tests', 'A-mapper.ecore')
    uri_mapper['plateforme://sibling'] = os.path.join('.')

    xmi_file = os.path.join('tests', 'xmi', 'xmi-tests', 'A-mapper2.ecore')
    resource = rset.get_resource(xmi_file)
    root = resource.contents[0]

    f = tmpdir.mkdir('pyecore-tmp').join('mapper.xmi')
    resource = rset.create_resource(str(f))
    resource.append(root)
    resource.save()
    rset.remove_resource(resource)

    resource = rset.get_resource(str(f))
    assert len(resource.contents) == 1

    root = resource.contents[0]
    # assert root.eClassifiers[0].eStructuralFeatures[0].eType.name == 'B'
    # assert root.eClassifiers[1].eStructuralFeatures[0].eType.name == 'EString'
    # assert root.eClassifiers[2].eStructuralFeatures[0].eType.name == 'A'
    #
    # with pytest.raises(Exception):
    #     root.eClassifiers[2].eStructuralFeatures[1].eType.name


def test_xmi_with_iD_attribute(tmpdir):
    mm_file = os.path.join('tests', 'xmi', 'xmi-tests', 'A.ecore')
    rset = ResourceSet()
    mm = rset.get_resource(mm_file).contents[0]
    rset.metamodel_registry[mm.nsURI] = mm

    mm_dyn = DynamicEPackage(mm)
    root = mm_dyn.Root()
    a = mm_dyn.A()
    b = mm_dyn.B()
    b.nameID = 'uniqueNameForB'
    a.tob = b

    root.a.append(a)
    root.b.append(b)

    localdir = tmpdir.mkdir('pyecore-tmp')
    f1 = localdir.join('model_iD_simple.xmi')
    resource = rset.create_resource(str(f1))
    resource.append(root)
    resource.save()

    root2 = mm_dyn.Root()
    root2.b.append(b)

    f2 = localdir.join('model_iD.xmi')
    f3 = localdir.join('model_iD.xmi')
    resource = rset.create_resource(str(f2))
    resource2 = rset.create_resource(str(f3))

    resource.append(root)
    resource2.append(root2)

    resource2.save()
    resource.save()

    rset = ResourceSet()
    rset.metamodel_registry[mm.nsURI] = mm
    rset.get_resource(str(f1))
    rset.get_resource(str(f2))
    rset.get_resource(str(f3))
