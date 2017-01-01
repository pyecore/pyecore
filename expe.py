import pprint
from uuid import uuid4
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

xsi_url = 'http://www.w3.org/2001/XMLSchema-instance'
xsi_prefix = 'xsi'
def go_accross(root):
    if not root.eContainmentFeature():
        prefix = root.eClass.ePackage.nsPrefix
        nsURI = root.eClass.ePackage.nsURI
        root_node = etree.QName(nsURI, root.eClass.name)
        nsmap = {'xmi': 'http://www.omg.org/XMI',
                 xsi_prefix: xsi_url,
                 prefix: nsURI}
        node = etree.Element(root_node, nsmap=nsmap)
        xmi_version = etree.QName('http://www.omg.org/XMI', 'version')
        node.attrib[xmi_version] = '2.0'
    else:
        node = etree.Element(root.eContainmentFeature().name)
        if root.eContainmentFeature().eType != root.eClass:
            xsi_type = etree.QName(xsi_url, 'type')
            prefix = root.eClass.ePackage.nsPrefix
            node.attrib[xsi_type] = '{0}:{1}'.format(prefix, root.eClass.name)
    for feat in root._isset:
        value = root.__getattribute__(feat.name)
        if isinstance(feat, Ecore.EAttribute):
            if feat.many and value:
                node.attrib[feat.name] = ' '.join(value)
            elif value != feat.get_default_value():
                node.attrib[feat.name] = str(value)
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

    # expe2
    # resource = rset.get_resource(URI('tests/xmi/xmi-tests/My.ecore'))
    # root = resource.contents[0]
    # print(list(root.eAllContents()))
    # global_registry[root.nsURI] = root
    # resource = rset.get_resource(URI('tests/xmi/xmi-tests/MyRoot.xmi'))
    # root = resource.contents[0]
    # # print(root._isset)
    # # print(root.aContainer)
    # A = root.aContainer[0].eClass
    # a1 = A()
    # a1.name = 'test'
    # root.aContainer.add(a1)
    # B = root.bContainer[0].eClass
    # b1 = B()
    # a1.b = b1
    # a1.name = None
    # root.bContainer.add(b1)
    # resource.save(output='test.xmi')
    #
    # resource = rset.get_resource('test.xmi')
    # root = resource.contents[0]
    # print(list(root.eAllContents()))

    # expe3
    resource = rset.get_resource(URI('tests/xmi/xmi-tests/My.ecore'))
    root = resource.contents[0]
    MyRoot = root.getEClassifier('MyRoot')
    A = root.getEClassifier('A')
    B = root.getEClassifier('B')

    myroot = MyRoot()
    a1 = A()
    a1.name = 'test'
    b1 = B()
    b1.a = a1
    myroot.aContainer.append(a1)
    myroot.bContainer.append(b1)

    resource = rset.create_resource(URI('test2.xmi'))
    resource.append(myroot)
    resource.save()
    print(b1.eResource)
