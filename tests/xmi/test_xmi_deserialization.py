import pytest
import pyecore.ecore as Ecore
from pyecore.resources import *
from pyecore.resources.xmi import XMIResource, XMIOptions
from pyecore.resources.resource import HttpURI, Resource
from pyecore.utils import DynamicEPackage
from os import path


# Modified to it does not need an internet connection anymore
def test_uri_http():
    uri = HttpURI('https://api.genmymodel.com/projects/_L0eC8P1oEeW9zv77lynsJg/xmi')
    assert uri.plain == 'https://api.genmymodel.com/projects/_L0eC8P1oEeW9zv77lynsJg/xmi'
    assert uri.protocol == 'https'
    assert uri.extension is None
    assert len(uri.segments) == 4
    assert uri.last_segment == 'xmi'
    assert uri.segments[0] == 'api.genmymodel.com'
    # flike = uri.create_instream()
    # assert flike.getcode() == 200
    with pytest.raises(NotImplementedError):
        uri.create_outstream()


def test_uri_simple():
    ecore_file = path.join('a', 'b', 'c.ecore')
    uri = URI(ecore_file)
    assert uri.plain == ecore_file
    assert uri.protocol is None
    assert uri.last_segment == 'c.ecore'
    assert uri.extension == 'ecore'


def test_xmiresource_load_ecore_testEMF():
    xmi_file = path.join('tests', 'xmi', 'xmi-tests', 'testEMF.xmi')
    resource = XMIResource(URI(xmi_file))
    resource.load()
    assert resource.contents != []
    root = resource.contents[0]
    A = root.getEClassifier('A')
    assert A
    B = root.getEClassifier('B')
    assert B
    TInterface = root.getEClassifier('TInterface')
    assert TInterface
    TClass = root.getEClassifier('TClass')
    assert TClass
    a = A()
    assert Ecore.EcoreUtils.isinstance(a, TClass)
    assert Ecore.EcoreUtils.isinstance(a, TInterface)
    assert A.findEStructuralFeature('abstract')
    assert A.findEStructuralFeature('isAbs')
    assert a.isAbs is False
    assert a.abstract is False
    assert a.eResource is None
    assert A.eResource is resource


def test_resourceset_getresource_ecore_My():
    rset = ResourceSet()
    ecore_file = path.join('tests', 'xmi', 'xmi-tests', 'My.ecore')
    resource = rset.get_resource(URI(ecore_file))
    assert resource.contents != []
    root = resource.contents[0]
    A = root.getEClassifier('A')
    B = root.getEClassifier('B')
    MyRoot = root.getEClassifier('MyRoot')
    assert A
    assert B
    assert MyRoot
    bRef = A.findEStructuralFeature('b')
    aRef = B.findEStructuralFeature('a')
    assert aRef.eOpposite is bRef


def test_resourceset_getresource_instance_MyRoot():
    rset = ResourceSet()
    # register the My.ecore metamodel in the resource set (could be in the global_registry)
    ecore_file = path.join('tests', 'xmi', 'xmi-tests', 'My.ecore')
    resource = rset.get_resource(URI(ecore_file))
    root = resource.contents[0]
    rset.metamodel_registry[root.nsURI] = root
    # load the instance model
    xmi_file = path.join('tests', 'xmi', 'xmi-tests', 'MyRoot.xmi')
    resource = rset.get_resource(URI(xmi_file))
    root = resource.contents[0]
    assert len(root.aContainer) == 2
    assert len(root.bContainer) == 1
    assert root.aContainer[0].b is root.bContainer[0]
    assert root.eResource is resource
    assert root.aContainer[0].eResource is resource
    assert root.eResource.resource_set is rset


def test_resourceset_getresource_ecore_Ecore():
     # load the ecore metamodel first
    rset = ResourceSet()
    ecore_file = path.join('tests', 'xmi', 'xmi-tests', 'Ecore.ecore')
    resource = rset.get_resource(URI(ecore_file))
    root = resource.contents[0]
    assert root
    assert root.getEClassifier('EClass')
    assert root.getEClassifier('EAttribute')
    assert root.getEClassifier('EReference')
    assert root.getEClassifier('EPackage')
    assert root.eResource is resource


def test_resourceset_getresource_ecore_UML():
    rset = ResourceSet()
    # # UMLPrimitiveTypes Metaclasses Creation
    # umltypes = Ecore.EPackage('umltypes')
    # String = Ecore.EDataType('String', str)
    # Boolean = Ecore.EDataType('Boolean', bool, False)
    # Integer = Ecore.EDataType('Integer', int, 0)
    # UnlimitedNatural = Ecore.EDataType('UnlimitedNatural', int, 0)
    # Real = Ecore.EDataType('Real', float, 0.0)
    # umltypes.eClassifiers.extend([String, Boolean, Integer, UnlimitedNatural, Real])
    # type_resource = rset.create_resource('platform:/plugin/org.eclipse.uml2.types/model/Types.ecore')
    # type_resource.append(umltypes)
    # Register Ecore metamodel as a model
    ecore_resource = rset.create_resource('platform:/plugin/org.eclipse.emf.ecore/model/Ecore.ecore')
    ecore_resource.append(Ecore.eClass)
    # Load the UML metamodel
    ecore_file = path.join('tests', 'xmi', 'xmi-tests', 'UML.ecore')
    resource = rset.get_resource(URI(ecore_file))
    root = resource.contents[0]
    assert root.getEClassifier('Class')
    assert root.getEClassifier('Interface')
    assert root.getEClassifier('State')
    assert root.eResource is resource


def test_ecoreinheritance_loading():
    rset = ResourceSet()
    ecore_file = path.join('tests', 'xmi', 'xmi-tests', 'EcoreInheritance.ecore')
    resource = rset.get_resource(URI(ecore_file))
    root = DynamicEPackage(resource.contents[0])
    assert Ecore.EModelElement.eAnnotations in root.A.eAllStructuralFeatures()
    a = root.A()
    assert isinstance(a, Ecore.EModelElement)
    assert Ecore.EModelElement.eAnnotations in root.B.eAllStructuralFeatures()
    b = root.B()
    assert isinstance(b, Ecore.EModelElement)
    assert a.eAnnotations == {}
    assert b.eAnnotations == {}


def test_ecore_nonhref_external_resources():
    rset = ResourceSet()
    c_ecore = path.join('tests', 'xmi', 'xmi-tests', 'inner', 'C.ecore')
    b_ecore = path.join('tests', 'xmi', 'xmi-tests', 'B.ecore')
    a_ecore = path.join('tests', 'xmi', 'xmi-tests', 'A.ecore')
    rset.get_resource(c_ecore)
    rset.get_resource(b_ecore)
    root = rset.get_resource(a_ecore).contents[0]
    assert root

    A = root.getEClassifier('A')
    assert A
    assert len(A.eSuperTypes) == 2


def test_resourceset_remove_resource():
    rset = ResourceSet()
    ecore_file = path.join('tests', 'xmi', 'xmi-tests', 'My.ecore')
    resource = rset.get_resource(URI(ecore_file))
    assert resource in rset.resources.values()

    rset.remove_resource(resource)
    assert resource not in rset.resources.values()


def test_resourceset_load_faulty_exception_no_resource():
    rset = ResourceSet()
    ecore_file = path.join('tests', 'xmi', 'xmi-tests', 'My_faulty.ecore')
    with pytest.raises(Exception):
        rset.get_resource(URI(ecore_file))
    assert rset.resources == {}

    with pytest.raises(Exception):
        rset.get_resource(URI(ecore_file))

    assert rset.resources == {}


def test_resourceset_load_no_prefix_resource():
    rset = ResourceSet()
    ecore_file = path.join('tests', 'xmi', 'xmi-tests', 'My_noprefix.ecore')
    root = rset.get_resource(URI(ecore_file)).contents[0]
    rset.metamodel_registry[root.nsURI] = root
    # load the instance model
    xmi_file = path.join('tests', 'xmi', 'xmi-tests', 'MyRoot_noprefix.xmi')
    resource = rset.get_resource(URI(xmi_file))
    root = resource.contents[0]
    assert root


def test_resourceset_load_faulty_exception_bad_metamodel():
    rset = ResourceSet()
    ecore_file = path.join('tests', 'xmi', 'xmi-tests', 'My_faulty2.ecore')
    with pytest.raises(Exception):
        rset.get_resource(ecore_file)


def test_ecore_nonhref_external_resources_autoload():
    rset = ResourceSet()
    a_ecore = path.join('tests', 'xmi', 'xmi-tests', 'A.ecore')
    root = rset.get_resource(a_ecore).contents[0]
    assert root

    A = root.getEClassifier('A')
    assert A
    assert len(A.eSuperTypes) == 2


def test_xmi_ecore_load_option_xmitype():
    rset = ResourceSet()
    a_ecore = path.join('tests', 'xmi', 'xmi-tests', 'My2.ecore')
    root = rset.get_resource(a_ecore).contents[0]
    assert root

    A = root.getEClassifier('A')
    assert A
    assert len(A.eStructuralFeatures) == 2


def test_ecore_attribute_at_root():
    rset = ResourceSet()
    a_ecore = path.join('tests', 'xmi', 'xmi-tests', 'A.ecore')
    root = rset.get_resource(a_ecore).contents[0]
    assert root
    rset.metamodel_registry[root.nsURI] = root

    a_xmi = path.join('tests', 'xmi', 'xmi-tests', 'a4.xmi')
    root = rset.get_resource(a_xmi).contents[0]
    assert root
    assert root.visible
    assert root.refa is root.a[0]


def test_deserialize_href_uuid_ref():
    Root = Ecore.EClass('Root')
    Root.eStructuralFeatures.append(Ecore.EReference('element', Ecore.EObject))
    pack = Ecore.EPackage('mypack', nsURI='http://mypack/1.0',
                          nsPrefix='mypack_pref')
    pack.eClassifiers.append(Root)

    rset = ResourceSet()

    resource = rset.get_resource('tests/xmi/xmi-tests/My.ecore')
    root = resource.contents[0]
    rset.metamodel_registry[root.nsURI] = root
    rset.metamodel_registry[pack.nsURI] = pack

    resource = rset.get_resource('tests/xmi/xmi-tests/encoded.xmi')
    root1 = resource.contents[0]
    resource = rset.get_resource('tests/xmi/xmi-tests/encoded2.xmi')
    root2 = resource.contents[0]
    assert root2.element.eClass is root1.eClass


def test_load_nill_values():
    rset = ResourceSet()
    mm_ecore = path.join('tests', 'xmi', 'xmi-tests', 'mm_for_nil.ecore')
    root = rset.get_resource(mm_ecore).contents[0]
    rset.metamodel_registry[root.nsURI] = root

    model = path.join('tests', 'xmi', 'xmi-tests', 'model_with_nil.xmi')
    root = rset.get_resource(model).contents[0]
    assert root
    set_features = [x.name for x in root._isset]
    assert 'name' in set_features
    assert 'element' in set_features
    assert root.name is None
    assert root.element is None


def test_load_empty_xmi():
    rset = ResourceSet()
    empty = path.join('tests', 'xmi', 'xmi-tests', 'empty.xmi')

    resource = rset.get_resource(empty)
    assert resource.contents == []


def test_load_multi_root_ecore():
    rset = ResourceSet()
    multi_root = path.join('tests', 'xmi', 'xmi-tests', 'multi_root.xmi')

    resource = rset.get_resource(multi_root)
    assert len(resource.contents) == 2

    root1 = resource.contents[0]
    assert root1.eClassifiers[0].name == 'A'

    root2 = resource.contents[1]
    assert root2.eClassifiers[0].name == 'B'

    A = root1.eClassifiers[0]
    B = root2.eClassifiers[0]
    assert B.findEStructuralFeature('to_a').eType is A


def test_load_multivalued_attribute():
    rset = ResourceSet()
    b_ecore = path.join('tests', 'xmi', 'xmi-tests', 'B.ecore')
    b_ecore_root = rset.get_resource(b_ecore).contents[0]
    rset.metamodel_registry[b_ecore_root.nsURI] = b_ecore_root

    b2_xmi = path.join('tests', 'xmi', 'xmi-tests', 'b2.xmi')
    root = rset.get_resource(b2_xmi).contents[0]
    assert root.names == ['abc', 'def', 'ghi']

    b3_xmi = path.join('tests', 'xmi', 'xmi-tests', 'b3.xmi')
    root = rset.get_resource(b3_xmi).contents[0]
    assert root.names == ['abc']


def test_load_multipleroot_with_refs():
    rset = ResourceSet()
    multi_root = path.join('tests', 'xmi', 'xmi-tests',
                           'multiple_with_refs.xmi')

    package = Ecore.EPackage('amm', 'ammuri', 'amm')
    A = Ecore.EClass('A')
    A.eStructuralFeatures.append(Ecore.EAttribute('name', Ecore.EString))
    A.eStructuralFeatures.append(Ecore.EReference('toa', A))
    A.eStructuralFeatures.append(Ecore.EReference('contains', A,
                                                  containment=True))
    package.eClassifiers.append(A)

    rset.metamodel_registry[package.nsURI] = package
    resource = rset.get_resource(URI(str(multi_root)))

    root1, root2 = resource.contents
    assert root1.contains.toa is root2
    assert root1.name == 'root1'
    assert root2.name == 'root2'
    assert root1.contains.name == 'inner'


def test_load_xmi_node_attribute():
    rset = ResourceSet()
    b_ecore = path.join('tests', 'xmi', 'xmi-tests', 'B.ecore')
    b_ecore_root = rset.get_resource(b_ecore).contents[0]
    rset.metamodel_registry[b_ecore_root.nsURI] = b_ecore_root

    b4_xmi = path.join('tests', 'xmi', 'xmi-tests', 'b4.xmi')
    root = rset.get_resource(b4_xmi).contents[0]
    assert root.names == ['abc', 'def', '', '    ']


def test_load_xmi_missing_attribute():
    rset = ResourceSet()
    b_ecore = path.join('tests', 'xmi', 'xmi-tests', 'B.ecore')
    b_ecore_root = rset.get_resource(b_ecore).contents[0]
    rset.metamodel_registry[b_ecore_root.nsURI] = b_ecore_root

    b5_xmi = path.join('tests', 'xmi', 'xmi-tests', 'b5.xmi')
    with pytest.raises(Exception):
        root = rset.get_resource(b5_xmi).contents[0]


def test_load_xsi_schemaLocation():
    rset = ResourceSet()

    b_file = path.join('tests', 'xmi', 'xmi-tests', 'b6.xmi')
    resource = rset.get_resource(b_file)

    assert len(resource.contents) == 1


def test_load_xsi_schemaLocation_error():
    rset = ResourceSet()

    b_file = path.join('tests', 'xmi', 'xmi-tests', 'b7.xmi')
    with pytest.raises(Exception):
        rset.get_resource(b_file)


def test_load_xsi_schemaLocation_no_fragment():
    rset = ResourceSet()
    schema_file = path.join('tests', 'xmi', 'xmi-tests', 'test_schema.xmi')
    resource = rset.get_resource(schema_file)

    assert len(resource.contents) == 1


def test_load_xmi_metamodel_uri_mapper():
    rset = ResourceSet()
    uri_mapper = rset.uri_mapper
    uri_mapper['plateforme://eclipse.stuff'] = 'http://www.eclipse.org/emf/2002'
    uri_mapper['plateforme://test'] = path.join('..', 'xmi-tests', 'A-mapper.ecore')

    from pyecore.resources import global_uri_mapper
    global_uri_mapper['plateforme://sibling'] = path.join('.')

    xmi_file = path.join('tests', 'xmi', 'xmi-tests', 'A-mapper.ecore')
    resource = rset.get_resource(xmi_file)

    assert len(resource.contents) == 1

    root = resource.contents[0]
    assert root.eClassifiers[0].eStructuralFeatures[0].eType.name == 'B'
    assert root.eClassifiers[1].eStructuralFeatures[0].eType.name == 'EString'
    assert root.eClassifiers[2].eStructuralFeatures[0].eType.name == 'A'

    with pytest.raises(Exception):
        root.eClassifiers[2].eStructuralFeatures[1].eType.name


def test_load_xmi_simple_iD():
    a_ecore = path.join('tests', 'xmi', 'xmi-tests', 'A.ecore')
    rset = ResourceSet()
    mm = rset.get_resource(a_ecore).contents[0]
    rset.metamodel_registry[mm.nsURI] = mm

    xmi_file = path.join('tests', 'xmi', 'xmi-tests', 'model_iD_simple.xmi')
    root = rset.get_resource(xmi_file).contents[0]
    assert len(root.a) == 1
    assert len(root.b) == 1
    assert root.a[0].tob.nameID == 'uniqueNameForB'


def test_load_xmi_iD_multiple():
    a_ecore = path.join('tests', 'xmi', 'xmi-tests', 'A.ecore')
    rset = ResourceSet()
    mm = rset.get_resource(a_ecore).contents[0]
    rset.metamodel_registry[mm.nsURI] = mm

    xmi_file = path.join('tests', 'xmi', 'xmi-tests', 'model1_iD.xmi')
    root = rset.get_resource(xmi_file).contents[0]
    assert len(root.a) == 1
    assert len(root.b) == 0
    assert root.a[0].tob.nameID == 'uniqueNameForB'
