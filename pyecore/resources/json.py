"""
The json module introduces JSON resource and JSON parsing.
"""
import json
from .resource import Resource
from .. import ecore as Ecore


class JsonResource(Resource):
    def __init__(self, uri=None, use_uuid=False):
        super().__init__(uri, use_uuid)
        self._resolve_mem = {}
        self._resolve_later = []
        self._already_saved = []

    def save(self, output=None):
        root = self.contents[0]
        return json.dumps(self.to_dict(root), indent=2)

    def __uri_fragment(self, obj):
        if obj.eResource == self:
            use_id = self._use_uuid
        else:
            use_id = obj.eResource and obj.eResource._use_uuid
        if use_id:
            self._assign_uuid(obj)
            return obj._xmiid
        else:
            return obj.eURIFragment()

    def to_dict(self, obj, is_ref=False):
        def to_ref(obj):
            eclass = obj.eClass
            uri = '{}{}'.format(eclass.ePackage.nsURI,
                                obj.eClass.eURIFragment())
            ref = {'eClass': uri}
            resource_uri = obj.eResource.uri if obj.eResource else ''
            if resource_uri is None:
                resource_uri = ''
            ref['$ref'] = '{}{}'.format(resource_uri, self.__uri_fragment(obj))
            return ref

        def to_dict_eobject(obj):
            eclass = obj.eClass
            uri = '{}{}'.format(eclass.ePackage.nsURI, eclass.eURIFragment())
            d = {'eClass': uri}
            containingFeature = obj.eContainmentFeature()
            for attr in obj._isset:
                is_ereference = isinstance(attr, Ecore.EReference)
                is_ref = is_ereference and not attr.containment
                if is_ereference and attr.eOpposite:
                    if attr.eOpposite is containingFeature:
                        continue
                    if obj.eGet(attr) in self._already_saved:
                        continue
                value = obj.eGet(attr)
                if value == attr.get_default_value():
                    continue
                d[attr.name] = self.to_dict(value, is_ref=is_ref)
                if self._use_uuid:
                    if not obj._xmiid:
                        self._assign_uuid(obj)
                    d['uuid'] = obj._xmiid
            self._already_saved.append(obj)
            return d

        if isinstance(obj, Ecore.EObject):
            fun = to_ref if is_ref else to_dict_eobject
            return fun(obj)
        elif isinstance(obj, type) and issubclass(obj, Ecore.EObject):
            fun = to_ref if is_ref else to_dict_eobject
            return fun(obj.eClass)
        elif isinstance(obj, Ecore.ECollection):
            fun = to_ref if is_ref else self.to_dict
            return [fun(x) for x in obj]
        else:
            return obj

    def resolve(self, fragment, from_resource=None):
        fragment = self.normalize(fragment)
        if fragment in self._resolve_mem:
            return self._resolve_mem[fragment]
        if self._use_uuid:
            try:
                frag = fragment[1:] if fragment.startswith('#') \
                                    else fragment
                frag = frag[2:] if frag.startswith('//') else frag
                return self.uuid_dict[frag]
            except KeyError:
                pass
        result = None
        for root in self._contents:
            result = self._navigate_from(fragment, root)
            if result:
                self._resolve_mem[fragment] = result
                return result

    def load(self, value):
        json_value = value
        d = json.loads(json_value)
        root = self.to_obj(d)
        return root

    def to_obj(self, d, owning_feature=None, first=False):
        uri_eclass = d['eClass']
        is_ref = '$ref' in d
        if is_ref:
            return EProxy(path=d['$ref'], resource=self)
        excludes = ['eClass', '$ref', 'uuid']
        decoders = self._get_href_decoder(uri_eclass)
        eclass = decoders.resolve(uri_eclass, self)
        if eclass in (Ecore.EClass.eClass, Ecore.EClass):
            inst = eclass(d['name'])
            excludes.append('name')
        else:
            inst = eclass()
        if first:
            self.append(inst)

        def process_inst(inst, features):
            for feature, value in features:
                if isinstance(value, dict):
                    element = self.to_obj(value, owning_feature=feature)
                    if feature.eOpposite is not owning_feature:
                        inst.eSet(feature, element)
                elif isinstance(value, list):
                    elements = [self.to_obj(x, owning_feature=feature)
                                for x in value]
                    elements = [x for x in elements if x is not None]
                    collection = inst.eGet(feature)
                    if feature.eOpposite is not owning_feature:
                        collection.extend(elements)
                else:
                    inst.eSet(feature, value)

        eattributes = []
        ereferences = []
        eclass = inst.eClass
        for key, value in d.items():
            if key in excludes:
                continue
            feature = eclass.findEStructuralFeature(key)
            if not feature:
                raise ValueError('Unknown feature {} for object "{}"'
                                 .format(key, eClass))
            if isinstance(value, Ecore.EAttribute):
                eattributes.append((feature, value))
            else:
                ereferences.append((feature, value))
        process_inst(inst, eattributes)
        process_inst(inst, ereferences)
        return inst
