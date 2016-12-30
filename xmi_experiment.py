from lxml import etree
import pyecore.ecore as Ecore
from pyecore.resources import global_registry, ResourceSet, URI, Resource

# Register static Ecore metamodel
global_registry.setdefault(Ecore.nsURI, Ecore)

def _build_path(obj):
    if not obj.eContainmentFeature():
        return '/'
    feat = obj.eContainmentFeature()
    parent = obj.eContainer()
    name = feat.name
    # TODO decode root names (non '@' prefixed)
    if feat.many:
        index = parent.__getattribute__(name).index(obj)
        return '{0}/@{1}.{2}'.format(_build_path(parent), name, str(index))
    else:
        return '{0}/{1}'.format(_build_path(parent), name)



if __name__ == '__main__':
    # # UMLPrimitiveTypes Creation
    # umltypes = Ecore.EPackage('umltypes')
    # String = Ecore.EDataType('String', str)
    # Boolean = Ecore.EDataType('Boolean', bool, False)
    # Integer = Ecore.EDataType('Integer', int, 0)
    # UnlimitedNatural = Ecore.EDataType('UnlimitedNatural', int, 0)
    # Real = Ecore.EDataType('Real', float, 0.0)
    # umltypes.eClassifiers.extend([String, Boolean, Integer, UnlimitedNatural, Real])
    # global_registry['platform:/plugin/org.eclipse.uml2.types/model/Types.ecore'] = umltypes
    #
    # resource = XMIResource(URI('xmi-tests/Ecore.ecore'))
    # resource.load()
    # root = resource.contents[0]
    # global_registry['platform:/plugin/org.eclipse.emf.ecore/model/Ecore.ecore'] = root
    #
    # resource = XMIResource(URI('xmi-tests/UML.ecore'))
    # resource.load()
    # root = resource.contents[0]
    # Class = root.getEClassifier('Class')
    # Property = root.getEClassifier('Property')
    # Visibility = root.getEClassifier('VisibilityKind')
    # c = Class()
    # p = Property()
    # p.name = 'testing'
    # p.type = c
    # c.ownedAttribute.append(p)
    # assert p in c.ownedAttribute
    rset = ResourceSet()
    resource = rset.get_resource(URI('xmi-tests/Ecore.ecore'))
    print(resource.contents)
