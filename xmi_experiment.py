from lxml import etree
import pyecore.ecore as Ecore
from pyecore.resource import global_registry

global_registry.setdefault(Ecore.nsURI, Ecore)

tree = etree.parse('xmi-tests/testEMF.xmi')

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


def _navigate_from(path, start_obj):
    features = list(filter(None, path.split('/')))
    feat_info = [x.split('.') for x in features]
    obj = start_obj
    for feat in feat_info:
        key, index = feat if len(feat) > 1 else (feat[0], None)
        if key.startswith('@'):
            tmp_obj = obj.__getattribute__(key[1:])
            obj = tmp_obj[int(index)] if index else tmp_obj
        else:
            obj = obj.getEClassifier(key)


class XMIResource(object):
    xsitype = None
    def __init__(self, tree):
        self._tree = tree
        self.root = tree.getroot()
        self.uuid_dict = {}
        self.nsmap = self.root.nsmap
        self.reverse_nsmap = {v: k for k,v in self.nsmap.items()}
        XMIResource.xsitype = '{{{0}}}type'.format(self.nsmap['xsi'])
        self._init_modelroot()


    @property
    def contents(self):
        return self._contents

    def extract_namespace(tag):
        qname = etree.QName(tag)
        return qname.namespace, qname.localname

    def prefix2epackage(self, prefix):
        try:
            return global_registry[self.nsmap[prefix]]
        except Exception:
            return None

    def _type_attribute(self, node):
        return node.get(XMIResource.xsitype)

    def _init_modelroot(self):
        """
        Initializes the model root during XMI deserialization
        """
        nsURI, eclass_name = XMIResource.extract_namespace(self.root.tag)
        eobject = global_registry[nsURI].getEClassifier(eclass_name)
        if not eobject:
            raise TypeError({'{0} EClass does not exists'}.format(eclass_name))
        modelroot = eobject()
        self._contents = [modelroot]
        for key, value in self.root.attrib.items():
            namespace, att_name = XMIResource.extract_namespace(key)
            prefix = self.reverse_nsmap[namespace] if namespace else None
            if prefix == 'xmi' and att_name == 'id':
                modelroot._xmiid = value
                self.uuid_dict[value] = modelroot
            elif namespace:
                try:
                    metaclass = global_registry[namespace]
                    print(metaclass.eClass.findEStructuralFeature(att_name))
                except KeyError:
                    pass
            elif not namespace:
                feature = eobject.eClass.findEStructuralFeature(key)
                if not feature:
                    continue
                modelroot.__setattr__(key, value)
        for child in self.root:
            self._do_extract(child, modelroot)

    def _do_extract(self, current_node, parent_eobj):
        if not self.contents:
            return
        eobject_info = self._decode_node(parent_eobj, current_node)
        feat_container, eobject, eatts, erefs = eobject_info

        # deal with eattributes and ereferences
        for eattribute, value in eatts:
            if eattribute.many:
                print('Later for', eattribute.name, value)
                continue
            print('set', eattribute.name, 'to', value)
            eobject.__setattr__(eattribute.name, value)
        for ereference, value in erefs:
            print('values', value)
            if ereference.many:
                print('Many Later for', ereference.name, value.split())
                continue
            print('set later', ereference.name, 'with', value)

        # attach the new eobject to the parent one
        if feat_container and feat_container.many:
            parent_eobj.__getattribute__(feat_container.name).append(eobject)
        elif feat_container:
            parent_eobj.__setattr__(feat_container.name, eobject)

        if eobject:
            print('MyPath', _build_path(eobject))

        # iterate on children
        for child in current_node:
            self._do_extract(child, eobject)

    def _decode_node(self, parent_eobj, node):
        feature_container = parent_eobj.eClass.findEStructuralFeature(node.tag)
        if self._type_attribute(node):
            prefix, _type = node.get(XMIResource.xsitype).split(':')
            if node.get('href'):
                print('Ref stuff for', _type)
                print('info', node.get('href'))
                print('will be put in', parent_eobj)
                print()
                return (None, None, [], [])
            if not prefix:
                raise ValueError('Prefix {0} is not registered'.format(prefix))
            epackage = self.prefix2epackage(prefix)
            etype = epackage.getEClassifier(_type)
            if not etype:
                raise ValueError('Type {0} is unknown in {1}'.format(_type,
                                                                     epackage))
        else:
            etype = feature_container.eType
        if not feature_container:
            raise ValueError('Feature {0} is unknown for {1}'
                             .format(node.tag, parent_eobj.eClass.name))
        # we create the instance
        if etype is Ecore.EClass:
            name = node.get('name')
            eobject = etype(name)
        else:
            eobject = etype()
        # we sort the node feature (no containments)
        eatts = []
        erefs = []
        for key, value in node.attrib.items():
            feature = self._decode_attribute(eobject, key, value)
            if not feature:
                print('key', key, 'val', value)
                continue  # we skipp the unknown feature
            if etype is Ecore.EClass and feature.name == 'name':
                continue  # we skip the name for metamodel import
            if isinstance(feature, Ecore.EAttribute):
                eatts.append((feature, value))
            else:
                erefs.append((feature, value))
        return (feature_container, eobject, eatts, erefs)

    def _decode_attribute(self, owner, key, value):
        namespace, att_name = XMIResource.extract_namespace(key)
        prefix = self.reverse_nsmap[namespace] if namespace else None
        # This is a special case, we are working with uuids
        if prefix == 'xmi' and att_name == 'id':
            owner._xmiid = value
            self.uuid_dict[value] = owner
        elif prefix == 'xsi' and att_name == 'type':
            # type has already been handled
            pass
        elif namespace:
            print(key, 'from', namespace, 'to', value)
        elif not namespace:
            feature = owner.eClass.findEStructuralFeature(att_name)
            if not feature:
                raise ValueError('Feature {0} does not exists for type {1}'
                                 .format(att_name, owner.eClass.name))
            return feature


    def _build_instance(self, metaclass):
        pass


resource = XMIResource(tree)
root = resource.contents[0]
print(root.nsURI)
print(root.eClassifiers[0].eAttributes[1].name)
x = root.eClassifiers[0]()
print(x.isAbs)
print(_build_path(root.eClassifiers[0].eAttributes[1]))

_navigate_from('//@eClassifiers.0/@eStructuralFeatures.1', root)
