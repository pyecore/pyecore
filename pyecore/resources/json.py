"""
The json module introduces JSON resource and JSON parsing.
"""
from enum import unique, Enum
from functools import lru_cache
import json
from .resource import Resource
from .. import ecore as Ecore


@unique
class JsonOptions(Enum):
    SERIALIZE_DEFAULT_VALUES = 0


class JsonResource(Resource):
    def __init__(self, uri=None, use_uuid=False, indent=None, ref_tag='$ref'):
        super().__init__(uri, use_uuid)
        self._resolve_later = []
        self._already_saved = []
        self._load_href = {}
        self.indent = indent
        self.ref_tag = ref_tag

    def load(self, options=None):
        json_value = self.uri.create_instream()
        d = json.loads(json_value.read().decode('utf-8'))
        self.to_obj(d, first=True)
        self.uri.close_stream()
        for inst, refs in self._load_href.items():
            self.process_inst(inst, refs)
        self._load_href.clear()

    def save(self, output=None, options=None):
        self.options = options or {}
        stream = self.open_out_stream(output)
        root = self.contents[0]  # Only single root atm
        stream.write(json.dumps(self.to_dict(root), indent=self.indent)
                     .encode('utf-8'))
        self.uri.close_stream()
        self.options = None

    def _uri_fragment(self, obj):
        if obj.eResource == self:
            use_id = self.use_uuid
        else:
            use_id = obj.eResource and obj.eResource.use_uuid
        if use_id:
            self._assign_uuid(obj)
            return obj._xmiid
        else:
            return obj.eURIFragment()

    def serialize_eclass(self, eclass):
        return '{}{}'.format(eclass.eRoot().nsURI, eclass.eURIFragment())

    def _to_ref_from_obj(self, obj):
        uri = self.serialize_eclass(obj.eClass)
        ref = {'eClass': uri}
        if obj.eResource == self:
            resource_uri = ''
        else:
            resource_uri = obj.eResource.uri if obj.eResource else ''
        ref[self.ref_tag] = '{}{}'.format(resource_uri,
                                          self._uri_fragment(obj))
        return ref

    def _to_dict_from_obj(self, obj):
        d = {}
        containingFeature = obj.eContainmentFeature()
        if not containingFeature or obj.eClass is not containingFeature.eType:
            uri = self.serialize_eclass(obj.eClass)
            d['eClass'] = uri
        for attr in obj._isset:
            is_ereference = isinstance(attr, Ecore.EReference)
            is_ref = is_ereference and not attr.containment
            if is_ereference and attr.eOpposite:
                if attr.eOpposite is containingFeature:
                    continue
            value = obj.eGet(attr)
            serialize_default_option = JsonOptions.SERIALIZE_DEFAULT_VALUES
            if (not self.options.get(serialize_default_option, False) and
                    value == attr.get_default_value()):
                continue
            d[attr.name] = self.to_dict(value, is_ref=is_ref)
            if self.use_uuid:
                self._assign_uuid(obj)
                d['uuid'] = obj._xmiid
        self._already_saved.append(obj)
        return d

    def to_dict(self, obj, is_ref=False):
        if isinstance(obj, Ecore.EObject):
            fun = self._to_ref_from_obj if is_ref else self._to_dict_from_obj
            return fun(obj)
        elif isinstance(obj, type) and issubclass(obj, Ecore.EObject):
            fun = self._to_ref_from_obj if is_ref else self._to_dict_from_obj
            return fun(obj.eClass)
        elif isinstance(obj, Ecore.ECollection):
            fun = self._to_ref_from_obj if is_ref else self.to_dict
            return [fun(x) for x in obj]
        else:
            return obj

    @lru_cache()
    def resolve_eclass(self, uri_eclass):
        decoders = self._get_href_decoder(uri_eclass)
        return decoders.resolve(uri_eclass, self)

    def to_obj(self, d, owning_feature=None, first=False):
        is_ref = self.ref_tag in d
        if is_ref:
            return Ecore.EProxy(path=d[self.ref_tag], resource=self)
        excludes = ['eClass', self.ref_tag, 'uuid']
        if 'eClass' in d:
            uri_eclass = d['eClass']
            eclass = self.resolve_eclass(uri_eclass)
        else:
            eclass = owning_feature.eType
        if not eclass:
            raise ValueError('Unknown metaclass for uri "{}"'
                             .format(uri_eclass))
        if eclass in (Ecore.EClass.eClass, Ecore.EClass):
            inst = eclass(d['name'])
            excludes.append('name')
        else:
            inst = eclass()
        if first:
            self.use_uuid = 'uuid' in d
            self.append(inst)

        if self.use_uuid:
            self.uuid_dict[d['uuid']] = inst

        eattributes = []
        containments = []
        ereferences = []
        eclass = inst.eClass
        for key, value in d.items():
            if key in excludes:
                continue
            feature = eclass.findEStructuralFeature(key)
            if not feature:
                raise ValueError('Unknown feature {} for object "{}"'
                                 .format(key, eclass))
            if isinstance(feature, Ecore.EAttribute):
                eattributes.append((feature, value))
            elif isinstance(feature, Ecore.EReference):
                if feature.containment:
                    containments.append((feature, value))
                else:
                    ereferences.append((feature, value))
        self.process_inst(inst, eattributes)
        self.process_inst(inst, containments, owning_feature)
        self._load_href[inst] = ereferences
        return inst

    def process_inst(self, inst, features, owning_feature=None):
        for feature, value in features:
            if isinstance(value, dict):
                element = self.to_obj(value, owning_feature=feature)
                if feature.eOpposite is None or \
                        feature.eOpposite is not owning_feature:
                    inst.eSet(feature, element)
            elif isinstance(value, list):
                elements = [self.to_obj(x, owning_feature=feature)
                            for x in value]
                elements = [x for x in elements if x is not None]
                collection = inst.eGet(feature)
                if feature.eOpposite is None or \
                        feature.eOpposite is not owning_feature:
                    collection.extend(elements)
            elif isinstance(value, str):
                inst.eSet(feature, feature.eType.from_string(value))
            else:
                inst.eSet(feature, value)
