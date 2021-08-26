# -*- coding: future_fstrings -*-
"""
The xmi module introduces XMI resource and XMI parsing.
"""
from enum import unique, Enum
from functools import lru_cache
from lxml.etree import parse, QName, Element, SubElement, ElementTree
from .resource import Resource
from ..ecore import EClass, EStringToStringMapEntry, EAnnotation, EProxy, \
                    EDataType

XSI = 'xsi'
XSI_URL = 'http://www.w3.org/2001/XMLSchema-instance'
XMI = 'xmi'
XMI_URL = 'http://www.omg.org/XMI'


@unique
class XMIOptions(Enum):
    OPTION_USE_XMI_TYPE = 0
    SERIALIZE_DEFAULT_VALUES = 1


class XMIResource(Resource):
    def __init__(self, uri=None, use_uuid=False):
        super().__init__(uri, use_uuid)
        self._later = []
        self.prefixes = {}
        self.reverse_nsmap = {}

    def load(self, options=None):
        self.options = options or {}
        self.cache_enabled = True
        tree = parse(self.uri.create_instream())
        xmlroot = tree.getroot()
        self.prefixes.update(xmlroot.nsmap)
        self.reverse_nsmap = {v: k for k, v in self.prefixes.items()}

        self.xsitype = f'{{{self.prefixes.get(XSI)}}}type'
        self.xmiid = f'{{{self.prefixes.get(XMI)}}}id'
        self.schema_tag = f'{{{self.prefixes.get(XSI)}}}schemaLocation'

        # Decode the XMI
        if f'{{{self.prefixes.get(XMI)}}}XMI' == xmlroot.tag:
            real_roots = xmlroot
        else:
            real_roots = [xmlroot]

        def grouper(iterable):
            args = [iter(iterable)] * 2
            return zip(*args)

        self.schema_locations = {}
        schema_tag_list = xmlroot.attrib.get(self.schema_tag, '')
        for prefix, path in grouper(schema_tag_list.split()):
            if '#' not in path:
                path = path + '#'
            self.schema_locations[prefix] = EProxy(path, self)

        for root in real_roots:
            modelroot = self._init_modelroot(root)
            for child in root:
                self._decode_eobject(child, modelroot)

        if self.contents:
            self._decode_ereferences()

        self._clean_registers()
        self.uri.close_stream()

    def xsi_type_url(self):
        if self.options.get(XMIOptions.OPTION_USE_XMI_TYPE, False):
            return XMI_URL
        return XSI_URL

    @staticmethod
    def extract_namespace(tag):
        qname = QName(tag)
        return qname.namespace, qname.localname

    def _type_attribute(self, node):
        type_ = node.get(self.xsitype)
        if type_ is None:
            xmi_type_url = f'{{{self.prefixes.get(XMI)}}}type'
            type_ = node.get(xmi_type_url)
        return type_

    def _get_metaclass(self, nsURI, eclass_name):
        try:
            return self.get_metamodel(nsURI).getEClassifier(eclass_name)
        except Exception as e:
            proxy = self.schema_locations[nsURI]
            try:
                return proxy.getEClassifier(eclass_name)
            except Exception:
                raise e

    def _init_modelroot(self, xmlroot):
        nsURI, eclass_name = self.extract_namespace(xmlroot.tag)
        eclass = self._get_metaclass(nsURI, eclass_name)
        if not eclass:
            raise TypeError(f'"{eclass_name}" EClass does not exists '
                            f'(line {xmlroot.tag})')
        modelroot = eclass()
        modelroot._eresource = self
        self.use_uuid = xmlroot.get(self.xmiid) is not None
        self.contents.append(modelroot)
        erefs = []
        for key, value in xmlroot.attrib.items():
            namespace, _ = self.extract_namespace(key)
            if key == self.xmiid:
                modelroot._internal_id = value
                self.uuid_dict[value] = modelroot
            # Do stuff with this
            # elif namespace:
            #     try:
            #
            #         # metaclass = self.get_metamodel(namespace)
            #         pass
            #     except KeyError:
            #         pass
            elif not namespace:
                feature = self._find_feature(modelroot.eClass, key)
                if not feature:
                    continue
                if feature.is_attribute:
                    self._decode_eattribute_value(modelroot, feature, value)
                    if feature.iD:
                        self.uuid_dict[value] = modelroot
                else:
                    erefs.append((feature, value))
        if erefs:
            self._later.append((modelroot, erefs))
        return modelroot

    @staticmethod
    def _decode_eattribute_value(eobject, eattribute, value, from_tag=False):
        is_many = eattribute.many
        if is_many and not from_tag:
            values = value.split()
            from_string = eattribute._eType.from_string
            results = [from_string(x) for x in values]
            eobject.__getattribute__(eattribute.name).extend(results)
        elif is_many:
            value = eattribute._eType.from_string(value)
            eobject.__getattribute__(eattribute.name).append(value)
        else:
            val = eattribute._eType.from_string(value)
            eobject.__setattr__(eattribute.name, val)

    def _decode_eobject(self, current_node, parent_eobj):
        eobject_info = self._decode_node(parent_eobj, current_node)
        feat_container, eobject, eatts, erefs, from_tag = eobject_info

        # deal with eattributes and ereferences
        for eattribute, value in eatts:
            self._decode_eattribute_value(eobject, eattribute, value, from_tag)

        if erefs:
            self._later.append((eobject, erefs))

        if not feat_container:
            return

        # attach the new eobject to the parent one
        if feat_container.many:
            parent_eobj.__getattribute__(feat_container.name).append(eobject)
        else:
            parent_eobj.__setattr__(feat_container.name, eobject)

        # iterate on children
        for child in current_node:
            self._decode_eobject(child, eobject)

    def _is_none_node(self, node):
        return f'{{{XSI_URL}}}nil' in node.attrib

    def _decode_node(self, parent_eobj, node):
        _, node_tag = self.extract_namespace(node.tag)
        feature_container = self._find_feature(parent_eobj.eClass, node_tag)
        if not feature_container:
            raise ValueError(f'Feature "{node_tag}" is unknown '
                             f'for {parent_eobj.eClass.name}, '
                             f'line {node.sourceline}')
        if self._is_none_node(node):
            if feature_container.many:
                parent_eobj.__getattribute__(feature_container.name) \
                           .append(None)
            else:
                parent_eobj.__setattr__(feature_container.name, None)

            return (None, None, [], [], False)
        if node.get('href'):
            ref = node.get('href')
            proxy = EProxy(path=ref, resource=self)
            return (feature_container, proxy, [], [], False)
        if self._type_attribute(node):
            prefix, _type = self._type_attribute(node).split(':')
            if not prefix:
                raise ValueError(f'Prefix {prefix} is not registered, '
                                 f'{node.tag} line {node.sourceline}')
            epackage = self.prefix2epackage(prefix)
            etype = epackage.getEClassifier(_type)
            if not etype:
                raise ValueError(f'Type {_type} is unknown in {epackage}, '
                                 f'{node.tag} line {node.sourceline}')
        else:
            etype = feature_container._eType
            if isinstance(etype, EProxy):
                etype.force_resolve()

        # we create the instance
        if etype is EClass or etype is EClass.eClass:
            name = node.get('name')
            eobject = etype(name)
        elif (etype is EStringToStringMapEntry
              or etype is EStringToStringMapEntry.eClass) \
                and feature_container is EAnnotation.details:
            annotation_key = node.get('key')
            annotation_value = node.get('value')
            parent_eobj.details[annotation_key] = annotation_value
            if annotation_key == 'documentation':
                container = parent_eobj.eContainer()
                if hasattr(container, 'python_class'):
                    container = container.python_class
                container.__doc__ = annotation_value
            return (None, None, tuple(), tuple(), False)
        elif isinstance(etype, EDataType):
            value = node.text if node.text else ''
            return (None, parent_eobj, ((feature_container, value),),
                    tuple(), True)
        else:
            # idref = node.get(f'{{{XMI_URL}}}idref')
            # if idref:
            #     return (None, parent_eobj, [],
            #             [(feature_container, idref)], True)
            eobject = etype()

        # we sort the node feature (no containments)
        eatts = []
        erefs = []
        for key, value in node.attrib.items():
            feature = self._decode_attribute(eobject, key, value, node)
            if not feature:
                continue  # we skip the unknown features
            if etype is EClass and feature.name == 'name':
                continue  # we skip the name for metamodel import
            if feature.is_attribute:
                eatts.append((feature, value))
                if feature.iD:
                    self.uuid_dict[value] = eobject
            else:
                erefs.append((feature, value))
        return (feature_container, eobject, eatts, erefs, False)

    def _decode_attribute(self, owner, key, value, node):
        namespace, att_name = self.extract_namespace(key)
        prefix = self.reverse_nsmap[namespace] if namespace else None
        # This is a special case, we are working with uuids
        if key == self.xmiid:
            owner._internal_id = value
            self.uuid_dict[value] = owner
        elif prefix in ('xsi', 'xmi') and att_name == 'type':
            # type has already been handled
            pass
        # elif namespace:
        #     pass
        elif not namespace:
            if att_name == 'href':
                return
            feature = self._find_feature(owner.eClass, att_name)
            if not feature:
                raise ValueError(f'Feature {att_name} does not exists for '
                                 f'type {owner.eClass.name} '
                                 f'({node.tag} line {node.sourceline})')
            return feature

    def _decode_ereferences(self):
        opposite = []
        for eobject, erefs in self._later:
            for ref, value in erefs:
                name = ref.name
                if name == 'eOpposite':
                    opposite.append((eobject, ref, value))
                    continue
                if ref.many:
                    values = [self.normalize(x) for x in value.split()]
                else:
                    values = [value]
                for value in values:
                    if not value:  # BA: Skip empty references
                        continue
                    resolved_value = self._resolve_nonhref(value)
                    if not resolved_value:
                        raise ValueError(f'EObject for {value} is unknown')
                    if not hasattr(resolved_value, '_inverse_rels'):
                        resolved_value = resolved_value.eClass
                    if ref.many:
                        eobject.__getattribute__(name).append(resolved_value)
                    else:
                        eobject.__setattr__(name, resolved_value)

        for eobject, ref, value in opposite:
            resolved_value = self._resolve_nonhref(value)
            if not resolved_value:
                raise ValueError(f'EObject for {value} is unknown')
            eobject.__setattr__(ref.name, resolved_value)

    @lru_cache()
    def _resolve_nonhref(self, path):
        uri, fragment = self._is_external(path)
        if uri:
            cleaned_uri = uri + '#' + fragment
            if cleaned_uri in self._resolve_mem:
                return self._resolve_mem[cleaned_uri]
            proxy = EProxy(path=cleaned_uri, resource=self)
            self._resolve_mem[cleaned_uri] = proxy
            return proxy
        if fragment in self._resolve_mem:
            return self._resolve_mem[fragment]
        return self.resolve(fragment)

    def _clean_registers(self):
        self._later.clear()
        self._find_feature.cache_clear()
        self._resolve_nonhref.cache_clear()
        self._resolve_mem.clear()
        self.cache_enabled = False

    def register_nsmap(self, prefix, uri):
        if uri in self.reverse_nsmap:
            return
        if prefix not in self.prefixes:
            self.prefixes[prefix] = uri
            self.reverse_nsmap[uri] = prefix
            return
        same_prefix = [x for x in self.prefixes.keys() if x.startswith(prefix)]
        prefix = f'{prefix}_{len(same_prefix)}'
        self.prefixes[prefix] = uri
        self.reverse_nsmap[uri] = prefix

    def register_eobject_epackage(self, eobj):
        epackage = eobj.eClass.ePackage
        prefix = epackage.nsPrefix
        nsURI = epackage.nsURI
        self.register_nsmap(prefix, nsURI)

    def save(self, output=None, options=None):
        self.options = options or {}
        output = self.open_out_stream(output)
        self.prefixes.clear()
        self.reverse_nsmap.clear()

        serialize_default = \
            self.options.get(XMIOptions.SERIALIZE_DEFAULT_VALUES,
                             False)
        nsmap = {XMI: XMI_URL}

        if len(self.contents) == 1:
            root = self.contents[0]
            self.register_eobject_epackage(root)
            tmp_xmi_root = self._go_across(root, serialize_default)
        else:
            tag = QName(XMI_URL, 'XMI')
            tmp_xmi_root = Element(tag)
            for root in self.contents:
                root_node = self._go_across(root, serialize_default)
                tmp_xmi_root.append(root_node)

        # update nsmap with prefixes register during the nodes creation
        nsmap.update(self.prefixes)
        xmi_root = Element(tmp_xmi_root.tag, nsmap=nsmap)
        xmi_root[:] = tmp_xmi_root[:]
        xmi_root.attrib.update(tmp_xmi_root.attrib)
        xmi_version = QName(XMI_URL, 'version')
        xmi_root.attrib[xmi_version] = '2.0'
        tree = ElementTree(xmi_root)
        tree.write(output,
                   pretty_print=True,
                   xml_declaration=True,
                   encoding=tree.docinfo.encoding)
        output.flush()
        self.uri.close_stream()

    def _add_explicit_type(self, node, obj):
        self.prefixes[XSI] = XSI_URL
        xsi_type = QName(self.xsi_type_url(), 'type')
        uri = obj.eClass.ePackage.nsURI
        if uri not in self.reverse_nsmap:
            epackage = self.get_metamodel(uri)
            self.register_nsmap(epackage.nsPrefix, uri)
        prefix = self.reverse_nsmap[uri]
        node.attrib[xsi_type] = f'{prefix}:{obj.eClass.name}'

    def _build_none_node(self, feature_name):
        sub = Element(feature_name)
        xsi_null = QName(self.xsi_type_url(), 'nil')
        sub.attrib[xsi_null] = 'true'
        return sub

    def _go_across(self, obj, serialize_default=False):
        eclass = obj.eClass
        if not obj.eContainmentFeature():  # obj is the root
            epackage = eclass.ePackage
            nsURI = epackage.nsURI
            tag = QName(nsURI, eclass.name) if nsURI else eclass.name
            node = Element(tag)
        else:
            node = Element(obj.eContainmentFeature().name)
            if obj.eContainmentFeature()._eType != eclass:
                self._add_explicit_type(node, obj)

        if self.use_uuid:
            self._assign_uuid(obj)
            xmi_id = f'{{{XMI_URL}}}id'
            node.attrib[xmi_id] = obj._internal_id

        for feat in obj._isset:
            if feat.derived or feat.transient:
                continue
            feat_name = feat.name
            value = obj.__getattribute__(feat_name)
            if value is None:
                if serialize_default:
                    node.append(self._build_none_node(feat_name))
                continue
            if hasattr(feat._eType, 'eType') and feat._eType.eType is dict:
                for key, val in value.items():
                    entry = Element(feat_name)
                    entry.attrib['key'] = key
                    entry.attrib['value'] = val
                    node.append(entry)
            elif feat.is_attribute:
                etype = feat._eType
                if feat.many and value:
                    to_str = etype.to_string
                    has_special_char = False
                    result_list = []
                    for v in value:
                        string = None if v is None else to_str(v)
                        if not string or any(x.isspace() for x in string):
                            has_special_char = True
                        result_list.append(string)
                    if has_special_char:
                        for v in result_list:
                            if v is None:
                                node.append(self._build_none_node(feat_name))
                            else:
                                sub = SubElement(node, feat_name)
                                sub.text = v
                    else:
                        node.attrib[feat_name] = ' '.join(result_list)
                    continue
                default_value = feat.get_default_value()
                if value != default_value or serialize_default:
                    node.attrib[feat_name] = etype.to_string(value)
                continue

            elif feat.is_reference and \
                    feat.eOpposite and feat.eOpposite.containment:
                continue
            elif feat.is_reference and not feat.containment:
                if feat.many:
                    results = [self._build_path_from(x) for x in value]
                    embedded = []
                    crossref = []
                    for i, result in enumerate(results):
                        frag, cref = result
                        if cref:
                            crossref.append((i, frag))
                        else:
                            embedded.append(frag)
                    if embedded:
                        result = ' '.join(embedded)
                        node.attrib[feat_name] = result
                    for i, ref in crossref:
                        sub = SubElement(node, feat_name)
                        sub.attrib['href'] = ref
                        self._add_explicit_type(sub, value[i])
                else:
                    frag, is_crossref = self._build_path_from(value)
                    if is_crossref:
                        sub = SubElement(node, feat_name)
                        sub.attrib['href'] = frag
                        self._add_explicit_type(sub, value)
                    else:
                        node.attrib[feat_name] = frag

            if feat.is_reference and feat.containment:
                children = value if feat.many else [value]
                for child in children:
                    node.append(self._go_across(child, serialize_default))
        return node
