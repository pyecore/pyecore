from lxml import etree
import pyecore.ecore as Ecore
from pyecore.resource import global_registry, ResourceSet

global_registry.setdefault(Ecore.nsURI, Ecore)

tree = etree.parse('xmi-tests/My.ecore')

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
    if '#' in path:
        path = path[1:]
    features = list(filter(None, path.split('/')))
    feat_info = [x.split('.') for x in features]
    obj = start_obj
    for feat in feat_info:
        key, index = feat if len(feat) > 1 else (feat[0], None)
        if key.startswith('@'):
            tmp_obj = obj.__getattribute__(key[1:])
            obj = tmp_obj[int(index)] if index else tmp_obj
        elif key.startswith('%'):
            return obj  # tmp
        else:
            try:
                obj = obj.getEClassifier(key)
            except AttributeError:
                feat = obj.findEStructuralFeature(key)
                if not feat:
                    obj = obj.findEOperation(key)
                else:
                    obj = feat
    return obj


class File_URI_decoder(object):
    def can_handle(path):
        return path.startswith('file://') or path.startswith('.')

    def resolve(path):
        pass


class Registered_URI_decoder(object):
    def can_handle(path):
        if ' ' in path:
            path = path.split()[-1:][0]
        fragment = path.split('#')
        if len(fragment) == 2:
            uri, fragment = fragment
        else:
            uri = None
        try:
            global_registry[uri]
            return True
        except KeyError:
            return False

    def resolve(path):
        if ' ' in path:
            path = path.split()[-1:][0]
        uri, fragment = path.split('#')
        epackage = global_registry[uri]
        return _navigate_from(fragment, epackage)


class XMIResource(object):
    xsitype = None
    _decoders = [File_URI_decoder, Registered_URI_decoder]

    def __init__(self, tree):
        self._tree = tree
        self.root = tree.getroot()
        self.uuid_dict = {}
        self.nsmap = self.root.nsmap
        self._use_uuid = False
        self.reverse_nsmap = {v: k for k,v in self.nsmap.items()}
        XMIResource.xsitype = '{{{0}}}type'.format(self.nsmap['xsi'])
        XMIResource.xmiid = '{{{0}}}id'.format(self.nsmap['xmi'])
        self._init_modelroot()
        print('INIT FINISHED')
        self._resourceset = None

    @property
    def resource_set(self):
        return self._resourceset

    @resource_set.setter
    def resource_set(self, rset):
        if self._resourceset:
            rset.resources.remove(self)
        self._resourceset = rset
        # dict not a list, URI should be used
        # rset.resources.append(self)

    def _get_decoder(self, path):
        if ' ' in path:
            path = path.split()[-1:][0]
        decoder = next((x for x in self._decoders if x.can_handle(path)), None)
        return decoder if decoder else self

    def resolve(self, fragment):
        if ' ' in fragment:
            fragment = fragment.split()[-1:][0]
        if fragment in self._resolve_mem:
            return self._resolve_mem[fragment]
        if self._use_uuid:
            try:
                frag = fragment[1:] if fragment.startswith('#') else fragment
                frag = frag[2:] if frag.startswith('//') else frag
                return self.uuid_dict[frag]
            except KeyError:
                pass
        result = None
        for root in self._contents:
            result = _navigate_from(fragment, root)
            if result:
                self._resolve_mem[fragment] = result
                print('add', fragment)
                return result

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
        self._use_uuid = self.root.get(XMIResource.xmiid) is not None
        self._contents = [modelroot]
        self._later = []
        self._resolve_mem = {}
        for key, value in self.root.attrib.items():
            namespace, att_name = XMIResource.extract_namespace(key)
            prefix = self.reverse_nsmap[namespace] if namespace else None
            if prefix == 'xmi' and att_name == 'id':
                modelroot._xmiid = value
                self.uuid_dict[value] = modelroot
            elif namespace:
                try:
                    metaclass = global_registry[namespace]
                except KeyError:
                    pass
            elif not namespace:
                feature = eobject.eClass.findEStructuralFeature(key)
                if not feature:
                    continue
                modelroot.__setattr__(key, value)
        for child in self.root:
            self._do_extract(child, modelroot)
        self._do_later_nodes()

    def _do_later_nodes(self):
        opposite = []
        for eobject, erefs in self._later:
            for ref, value in erefs:
                if ref.name == 'eOpposite':
                    opposite.append((eobject, ref, value))
                    continue
                if ref.many:
                    for val in value.split():
                        decoder = self._get_decoder(val)
                        resolved_value = decoder.resolve(val)
                        if not resolved_value:
                            raise ValueError('EObject for {0} is unknown'.format(value))
                        eobject.__getattribute__(ref.name) \
                               .append(resolved_value)
                    continue
                decoder = self._get_decoder(value)
                resolved_value = decoder.resolve(value)
                if not resolved_value:
                    raise ValueError('EObject for {0} is unknown'.format(value))
                eobject.__setattr__(ref.name, resolved_value)
        for eobject, ref, value in opposite:
            decoder = self._get_decoder(value)
            resolved_value = decoder.resolve(value)
            if not resolved_value:
                raise ValueError('EObject for {0} is unknown'.format(value))
            eobject.__setattr__(ref.name, resolved_value)

    def _do_extract(self, current_node, parent_eobj):
        if not self.contents:
            return
        eobject_info = self._decode_node(parent_eobj, current_node)
        feat_container, eobject, eatts, erefs = eobject_info
        if not feat_container:
            return

        # deal with eattributes and ereferences
        for eattribute, value in eatts:
            if eattribute.many:
                print('Later for', eattribute.name, value)
                continue
            eobject.__setattr__(eattribute.name, value)

        if erefs:
            self._later.append((eobject, erefs))

        # attach the new eobject to the parent one
        if feat_container and feat_container.many:
            parent_eobj.__getattribute__(feat_container.name).append(eobject)
        elif feat_container:
            parent_eobj.__setattr__(feat_container.name, eobject)

        # iterate on children
        for child in current_node:
            self._do_extract(child, eobject)

    def _decode_node(self, parent_eobj, node):
        if node.tag == 'eGenericType':
            return (None, None, [], [])
        feature_container = parent_eobj.eClass.findEStructuralFeature(node.tag)
        if not feature_container:
            raise ValueError('Feature {0} is unknown for {1}, line {2}'
                             .format(node.tag,
                                     parent_eobj.eClass.name,
                                     node.sourceline,))
        if self._type_attribute(node):
            prefix, _type = node.get(XMIResource.xsitype).split(':')
            if node.get('href'):
                ref = node.get('href')
                decoder = self._get_decoder(ref)
                return (feature_container, decoder.resolve(ref), [], [])
            if not prefix:
                raise ValueError('Prefix {0} is not registered'.format(prefix))
            epackage = self.prefix2epackage(prefix)
            etype = epackage.getEClassifier(_type)
            if not etype:
                raise ValueError('Type {0} is unknown in {1}'.format(_type,
                                                                     epackage))
        else:
            etype = feature_container.eType

        # we create the instance
        if etype is Ecore.EClass:
            name = node.get('name')
            eobject = etype(name)
        elif etype is Ecore.EStringToStringMapEntry \
             and feature_container is Ecore.EAnnotation.details:
            parent_eobj.details[node.get('key')] = node.get('value')
            return (None, None, [], [])
        else:
            eobject = etype()

        # we sort the node feature (no containments)
        eatts = []
        erefs = []
        for key, value in node.attrib.items():
            feature = self._decode_attribute(eobject, key, value)
            if not feature:
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
            pass
        elif not namespace:
            feature = owner.eClass.findEStructuralFeature(att_name)
            if not feature:
                raise ValueError('Feature {0} does not exists for type {1}'
                                 .format(att_name, owner.eClass.name))
            return feature


    def _build_instance(self, metaclass):
        pass


if __name__ == '__main__':
    # UMLPrimitiveTypes Creation
    umltypes = Ecore.EPackage('umltypes')
    String = Ecore.EDataType('String', str)
    Boolean = Ecore.EDataType('Boolean', bool, False)
    Integer = Ecore.EDataType('Integer', int, 0)
    UnlimitedNatural = Ecore.EDataType('UnlimitedNatural', int, 0)
    Real = Ecore.EDataType('Real', float, 0.0)
    umltypes.eClassifiers.extend([String, Boolean, Integer, UnlimitedNatural, Real])
    global_registry['platform:/plugin/org.eclipse.uml2.types/model/Types.ecore'] = umltypes

    tree = etree.parse('xmi-tests/Ecore.ecore')
    resource = XMIResource(tree)
    root = resource.contents[0]
    global_registry['platform:/plugin/org.eclipse.emf.ecore/model/Ecore.ecore'] = root

    tree = etree.parse('xmi-tests/UML.ecore')
    resource = XMIResource(tree)
    root = resource.contents[0]
    Class = root.getEClassifier('Class')
    c = Class()
    print(c.eClass.eAllStructuralFeatures())
