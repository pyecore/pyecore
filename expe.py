import pprint
from lxml import etree
import pyecore.ecore as Ecore
from pyecore.resources import *
from pyecore.resources.xmi import XMIResource

def _build_path(obj):
    if not obj.eContainmentFeature():
        return '/'
    if obj._xmiid:
        return obj._xmiid
    feat = obj.eContainmentFeature()
    parent = obj.eContainer()
    name = feat.name
    # TODO decode root names (non '@' prefixed)
    if feat.many:
        index = parent.__getattribute__(name).index(obj)
        return '{0}/@{1}.{2}'.format(_build_path(parent), name, str(index))
    else:
        return '{0}/{1}'.format(_build_path(parent), name)

def go_accross(root):
    if not root.eContainmentFeature():
        prefix = root.eClass.ePackage.nsPrefix
        nsURI = root.eClass.ePackage.nsURI
        root_node = etree.QName(nsURI, root.eClass.name)
        nsmap = {'xmi': 'http://www.omg.org/XMI',
                 'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                 prefix: nsURI,
                }
        node = etree.Element(root_node, nsmap=nsmap)
        xmi_version = etree.QName('http://www.omg.org/XMI', 'version')
        node.attrib[xmi_version] = '2.0'
        print(root_node)
    else:
        node = etree.Element(root.eContainmentFeature().name)
    for feat in root._isset:
        value = root.__getattribute__(feat.name)
        if isinstance(feat, Ecore.EAttribute):
            if feat.many:
                node.attrib[feat.name] = ' '.join(value)
            else:
                node.attrib[feat.name] = value
        elif isinstance(feat, Ecore.EReference) and not feat.containment:
            if feat.many:
                node.attrib[feat.name] = ' '.join(list(map(_build_path, value)))
            else:
                node.attrib[feat.name] = _build_path(value)
        if isinstance(feat, Ecore.EReference) and feat.containment and feat.many:
            children = root.__getattribute__(feat.name)
            for child in children:
                node.append(go_accross(child))
        elif isinstance(feat, Ecore.EReference) and feat.containment:
            child = root.__getattribute__(feat.name)
            node.append(go_accross(child))
    return node

if __name__ == '__main__':
    global_registry[Ecore.nsURI] = Ecore
    rset = ResourceSet()
    # # UMLPrimitiveTypes Creation
    # umltypes = Ecore.EPackage('umltypes')
    # String = Ecore.EDataType('String', str)
    # Boolean = Ecore.EDataType('Boolean', bool, False)
    # Integer = Ecore.EDataType('Integer', int, 0)
    # UnlimitedNatural = Ecore.EDataType('UnlimitedNatural', int, 0)
    # Real = Ecore.EDataType('Real', float, 0.0)
    # umltypes.eClassifiers.extend([String, Boolean, Integer, UnlimitedNatural, Real])
    # rset.resources['platform:/plugin/org.eclipse.uml2.types/model/Types.ecore'] = umltypes
    # # Register Ecore metamodel instance
    # resource = rset.get_resource(URI('tests/xmi/xmi-tests/Ecore.ecore'))
    # rset.resources['platform:/plugin/org.eclipse.emf.ecore/model/Ecore.ecore'] = resource.contents[0]
    # resource = rset.get_resource(URI('tests/xmi/xmi-tests/UML.ecore'))
    resource = rset.get_resource(URI('tests/xmi/xmi-tests/My.ecore'))
    global_registry[resource.contents[0].nsURI] = resource.contents[0]
    resource = rset.get_resource(URI('tests/xmi/xmi-tests/MyRoot.xmi'))
    root = resource.contents[0]
    # print(root._isset)
    # print(root.aContainer)
    tree = etree.ElementTree(go_accross(root))
    print(tree.docinfo.encoding)
    print(etree.tostring(tree, pretty_print=True,xml_declaration = True, encoding=tree.docinfo.encoding))
    print(etree.tounicode(tree, pretty_print=True))
