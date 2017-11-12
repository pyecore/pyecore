import pytest
import pyecore.ecore as Ecore
from pyecore.resources import *
from pyecore.resources.xmi import XMIResource
from pyecore.resources.resource import HttpURI
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
    global_registry[Ecore.nsURI] = Ecore
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
    global_registry[Ecore.nsURI] = Ecore
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
    global_registry[Ecore.nsURI] = Ecore
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
    global_registry[Ecore.nsURI] = Ecore
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
    global_registry[Ecore.nsURI] = Ecore
    rset = ResourceSet()
    # UMLPrimitiveTypes Metaclasses Creation
    umltypes = Ecore.EPackage('umltypes')
    String = Ecore.EDataType('String', str)
    Boolean = Ecore.EDataType('Boolean', bool, False)
    Integer = Ecore.EDataType('Integer', int, 0)
    UnlimitedNatural = Ecore.EDataType('UnlimitedNatural', int, 0)
    Real = Ecore.EDataType('Real', float, 0.0)
    umltypes.eClassifiers.extend([String, Boolean, Integer, UnlimitedNatural, Real])
    rset.resources['platform:/plugin/org.eclipse.uml2.types/model/Types.ecore'] = umltypes
    # Register Ecore metamodel as a model
    rset.resources['platform:/plugin/org.eclipse.emf.ecore/model/Ecore.ecore'] = Ecore
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
