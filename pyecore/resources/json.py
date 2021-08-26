# -*- coding: future_fstrings -*-
"""
The json module introduces JSON resource and JSON parsing.
"""
from enum import unique, Enum
from functools import lru_cache
import json
from .resource import Resource
from ..ecore import EObject, EProxy, ECollection, EClass, EEnumLiteral


@unique
class JsonOptions(Enum):
    SERIALIZE_DEFAULT_VALUES = 0


NO_OBJECT = object()


class JsonResource(Resource):
    def __init__(self, uri=None, use_uuid=False, indent=None, ref_tag='$ref'):
        super().__init__(uri, use_uuid)
        self._resolve_later = []
        self._load_href = {}
        self.indent = indent
        self.ref_tag = ref_tag
        self.mappers = {}
        self.default_mapper = DefaultObjectMapper()

    def load(self, options=None):
        self.cache_enabled = True
        json_value = self.uri.create_instream()
        d = json.loads(json_value.read().decode('utf-8'))
        if isinstance(d, list):
            for x in d:
                self.to_obj(x, first=True)
        else:
            self.to_obj(d, first=True)
        self.uri.close_stream()
        for inst, refs in self._load_href.items():
            self.process_inst(inst, refs)
        self._load_href.clear()
        self._find_feature.cache_clear()
        self.cache_enabled = False

    def save(self, output=None, options=None):
        self.options = options or {}
        stream = self.open_out_stream(output)
        dict_list = []
        for root in self.contents:
            dict_list.append(self.to_dict(root))
        if len(dict_list) <= 1:
            dict_list = dict_list[0]

        stream.write(json.dumps(dict_list, indent=self.indent)
                     .encode('utf-8'))
        stream.flush()
        self.uri.close_stream()
        self.options = None

    def _uri_fragment(self, obj):
        if obj.eResource == self:
            use_id = self.use_uuid
        else:
            use_id = obj.eResource and obj.eResource.use_uuid
        if use_id:
            self._assign_uuid(obj)
            return obj._internal_id
        else:
            return obj.eURIFragment()

    @staticmethod
    def serialize_eclass(eclass):
        return f'{eclass.eRoot().nsURI}{eclass.eURIFragment()}'

    def register_mapper(self, eclass, mapper_class):
        if hasattr(eclass, 'python_class'):
            eclass = eclass.python_class
        self.mappers[eclass] = mapper_class

    def object_uri(self, obj):
        if obj.eResource == self:
            resource_uri = ''
        else:
            resource_uri = obj.eResource.uri if obj.eResource else ''
        return f'{resource_uri}{self._uri_fragment(obj)}'

    def _to_ref_from_obj(self, obj, opts=None, use_uuid=None, resource=None):
        uri = self.serialize_eclass(obj.eClass)
        ref = {'eClass': uri}
        ref[self.ref_tag] = self.object_uri(obj)
        return ref

    def to_dict(self, obj, is_ref=False):
        if isinstance(obj, type) and issubclass(obj, EObject):
            if is_ref:
                fun = self._to_ref_from_obj
                return fun(obj.eClass, self.options, self.use_uuid, self)
            # else:
            #     cls = obj.python_class
            #     mapper = next((self.mappers[k] for k in self.mappers
            #                    if issubclass(cls, k)), self.default_mapper)
            #     fun = mapper.to_dict_from_obj
        elif isinstance(obj, EEnumLiteral):
            return obj.name
        elif isinstance(obj, EObject):
            if is_ref:
                fun = self._to_ref_from_obj
            else:
                cls = obj.eClass.python_class
                mapper = next((self.mappers[k] for k in self.mappers
                               if issubclass(cls, k)), self.default_mapper)
                fun = mapper.to_dict_from_obj
            return fun(obj, self.options, self.use_uuid, self)

        elif isinstance(obj, ECollection):
            fun = self._to_ref_from_obj if is_ref else self.to_dict
            result = []
            for x in obj:
                write_object = fun(x)
                if write_object is NO_OBJECT:
                    continue
                result.append(write_object)
            return result
        else:
            return obj

    @lru_cache()
    def resolve_eclass(self, uri_eclass):
        return self.resolve_object(uri_eclass)

    def to_obj(self, d, owning_feature=None, first=False):
        is_ref = self.ref_tag in d
        if is_ref:
            return EProxy(path=d[self.ref_tag], resource=self)
        excludes = ['eClass', self.ref_tag, 'uuid']
        if 'eClass' in d:
            uri_eclass = d['eClass']
            eclass = self.resolve_eclass(uri_eclass)
        else:
            eclass = owning_feature._eType
        if not eclass:
            raise ValueError(f'Unknown metaclass for uri "{uri_eclass}"')
        if eclass in (EClass.eClass, EClass):
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
            feature = self._find_feature(eclass, key)
            if not feature:
                raise ValueError('Unknown feature {key} for object "{eclass}"')
            if feature.is_attribute:
                eattributes.append((feature, value))
            else:
                if feature.containment:
                    containments.append((feature, value))
                elif feature.eOpposite is not owning_feature:
                    ereferences.append((feature, value))
        self.process_inst(inst, eattributes)
        self.process_inst(inst, containments, owning_feature)
        self._load_href[inst] = ereferences
        return inst

    def process_inst(self, inst, features, owning_feature=None):
        for feature, value in features:
            if isinstance(value, dict):
                element = self.to_obj(value, owning_feature=feature)
                inst.eSet(feature, element)
            elif isinstance(value, list):
                if feature.is_reference:
                    elements = [self.to_obj(x, owning_feature=feature)
                                for x in value]
                    elements = [x for x in elements if x is not None]
                else:
                    elements = [feature._eType.from_string(x) for x in value]
                inst.eGet(feature).extend(elements)
            elif isinstance(value, str):
                inst.eSet(feature, feature._eType.from_string(value))
            else:
                inst.eSet(feature, value)


class DefaultObjectMapper(object):
    def to_dict_from_obj(self, obj, options, use_uuid, resource):
        d = {}
        containingFeature = obj.eContainmentFeature()
        if not containingFeature or obj.eClass is not containingFeature._eType:
            uri = resource.serialize_eclass(obj.eClass)
            d['eClass'] = uri
        for attr in obj._isset:
            if attr.derived or attr.transient:
                continue
            is_ereference = attr.is_reference
            is_ref = is_ereference and not attr.containment
            if is_ereference and attr.eOpposite:
                if attr.eOpposite is containingFeature:
                    continue
            value = obj.eGet(attr)
            serialize_default_option = JsonOptions.SERIALIZE_DEFAULT_VALUES
            if (not options.get(serialize_default_option, False)
                    and value == attr.get_default_value()):
                continue
            write_object = resource.to_dict(value, is_ref=is_ref)
            if write_object is not NO_OBJECT:
                d[attr.name] = write_object
            if use_uuid:
                resource._assign_uuid(obj)
                d['uuid'] = obj._internal_id
        return d
