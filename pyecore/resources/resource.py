# -*- coding: future_fstrings -*-
""" The resource module proposes all the concepts that are related to Resource
handling. A Resource represents a special model container that can be
serialized. Many ``Resource`` can be contained in a ``ResourceSet``, and
"cross-reference" each others.
"""
from uuid import uuid4
import urllib.request
import re
from os import path
from itertools import chain
from collections import ChainMap
from .. import ecore as Ecore
from ..innerutils import ignored
from abc import abstractmethod
from urllib.parse import urljoin
from functools import lru_cache


global_registry = {}
global_uri_mapper = {}
global_uri_converter = []


class ResourceSet(object):
    """Defines a Resource container.

    A ResourceSet can contains many Resources and has the ability to create new
    ones. It also gives a way of isolating resources from each others and to
    "localy" register metamodels.

    Resource can be created empty (using ``create_resource(...)``) or with data
    fetched from the actual resource content (using ``get_resource(...)``).

    A :py:class:`ResourceSet` contains 3 handy properties:

    * ``resources`` which is a dictonary of the ResourceSet loaded resources
      (key is the plain string URI, value: the resource).
    * ``metamodel_registry`` which is a dictonary of the ResourceSet known
      metamodels (key is the plain string metamodel URI, value: the metamodel
      ``EPackage`` root)
    * ``resource_factory`` which is a factory used by the ResourceSet to build
      the right Resource kind regarding the URI.

    .. seealso:: Resource
    """

    def __init__(self):
        self.resources = {}
        self.metamodel_registry = ChainMap({}, global_registry)
        self.uri_mapper = ChainMap({}, global_uri_mapper)
        self.uri_converter = []
        self.resource_factory = dict(ResourceSet.resource_factory)

    def create_resource(self, uri):
        """Creates a new Resource.

        The created ressource type depends on the used URI.

        :param uri: the resource URI
        :type uri: URI
        :return: a new Resource
        :rtype: Resource

        .. seealso:: URI, Resource, XMIResource
        """
        if isinstance(uri, str):
            uri = URIConverter.convert(URI(uri))
        try:
            resource = self.resource_factory[uri.extension](uri)
        except KeyError:
            resource = self.resource_factory['*'](uri)
        self.resources[uri.normalize()] = resource
        resource.resource_set = self
        resource.decoders.insert(0, self)
        return resource

    def remove_resource(self, resource):
        if not resource:
            return
        for key, value in dict(self.resources).items():
            if value is resource:
                del self.resources[key]

    def get_resource(self, uri, options=None):
        if isinstance(uri, str):
            uri = URIConverter.convert(URI(uri))
        # We check first if the resource already exists in the ResourceSet
        if uri.normalize() in self.resources:
            return self.resources[uri.normalize()]
        # If not, we create a new resource
        resource = self.create_resource(uri)
        try:
            resource.load(options=options)
        except Exception:
            self.remove_resource(resource)
            raise
        return resource

    def can_resolve(self, uri_path, from_resource=None):
        uri_path = Resource.normalize(uri_path)
        fragment = uri_path.rsplit('#', maxsplit=1)
        nb_fragments = len(fragment)
        uri_str = ''
        if nb_fragments == 2:
            uri_str, fragment = fragment
            if uri_str in self.resources:
                return True
        start = from_resource.uri.normalize() if from_resource else '.'
        apath = path.dirname(start)
        uri = URI(path.join(apath, uri_str))
        return uri.normalize() in self.resources

    def resolve(self, uri, from_resource=None):
        upath = URIMapper.translate(Resource.normalize(uri), from_resource)
        uri_str, fragment = upath.rsplit('#', maxsplit=1)
        if uri_str in self.resources:
            root = self.resources[uri_str]
        else:
            start = from_resource.uri.normalize() if from_resource else '.'
            apath = path.dirname(start)
            uri = URI(path.join(apath, uri_str))
            root = self.resources[uri.normalize()]
        if isinstance(root, Resource):
            root_number, fragment = Resource.extract_rootnum_and_frag(fragment)
            root = root.contents[root_number]
        return Resource._navigate_from(fragment, root)


class URI(object):
    _uri_norm = {'http': lambda x: x,
                 'https': lambda x: x,
                 'file': lambda x: path.abspath(x.replace('file://', ''))}

    _uri_split = {'http': '/',
                  'https': '/',
                  'file': path.sep}

    def __init__(self, uri):
        if uri is None:
            raise TypeError('URI cannot be None')
        self.plain = uri
        self._split()
        self.__stream = None

    def _split(self):
        if '://' in self.plain:
            self._protocol, rest = self.plain.split('://', maxsplit=1)
        elif ':/' in self.plain:
            self._protocol, rest = self.plain.split(':/', maxsplit=1)
        else:
            self._protocol, rest = None, self.plain
        uri_sep = self._uri_split.get(self._protocol, path.sep)
        self._segments = rest.split(uri_sep)
        self._last_segment = self._segments[-1:][0]
        if '.' in self._last_segment:
            self._extension = self._last_segment.split('.')[-1:][0]
        else:
            self._extension = None

    @property
    def protocol(self):
        return self._protocol

    @property
    def extension(self):
        return self._extension

    @property
    def segments(self):
        return self._segments

    @property
    def last_segment(self):
        return self._last_segment

    def create_instream(self):
        self.__stream = open(self.plain, 'rb')
        return self.__stream

    def close_stream(self):
        if self.__stream:
            self.__stream.close()

    def create_outstream(self):
        self.__stream = open(self.plain, 'wb')
        return self.__stream

    def normalize(self):
        if self.protocol is not None:
            return self._uri_norm.get(self.protocol, lambda x: x)(self.plain)
        return path.abspath(self.plain)

    def relative_from_me(self, other_uri):
        normalized = path.dirname(self.normalize())
        if isinstance(other_uri, URI):
            other_normalized = other_uri.normalize()
            if other_uri.protocol:
                return other_normalized
        return path.relpath(other_normalized, normalized)

    def apply_relative_from_me(self, relative_path):
        if ':/' in relative_path:
            return relative_path
        parent_path = path.dirname(self.normalize())
        return path.join(parent_path, relative_path)


class HttpURI(URI):
    def __init__(self, uri):
        super().__init__(uri)

    def create_instream(self):
        self.__stream = urllib.request.urlopen(self.plain)
        return self.__stream

    def create_outstream(self):
        raise NotImplementedError('Cannot create an outstream for HttpURI')

    def apply_relative_from_me(self, relative_path):
        return urljoin(self.normalize(), relative_path)


# class StdioURI(URI):
#     def __init__(self):
#         super().__init__('stdio')
#
#     def create_instream(self):
#         self.__stream = sys.stdin.buffer
#         return self.__stream
#
#     def create_outstream(self):
#         self.__stream = sys.stdout.buffer
#         return self.__stream
#
#     def close_stream(self):
#         pass


class MetamodelDecoder(object):
    @staticmethod
    def split_path(path):
        path = Resource.normalize(path)
        fragment = path.rsplit('#', maxsplit=1)
        if len(fragment) == 2:
            uri, fragment = fragment
        else:
            uri = None
        return uri, fragment

    @staticmethod
    def can_resolve(path, registry):
        uri, _ = MetamodelDecoder.split_path(path)
        return uri in registry

    @staticmethod
    def resolve(path, registry):
        path = Resource.normalize(path)
        uri, fragment = path.rsplit('#', maxsplit=1)
        epackage = registry[uri]
        return Resource._navigate_from(fragment, epackage)


class Global_URI_decoder(object):
    @staticmethod
    def can_resolve(path, from_resource=None):
        return MetamodelDecoder.can_resolve(path, global_registry)

    @staticmethod
    def resolve(path, from_resource=None):
        path = URIMapper.translate(path, from_resource)
        return MetamodelDecoder.resolve(path, global_registry)


class URIMapper(object):
    @staticmethod
    def translate(path, from_resource=None):
        if from_resource is None or from_resource.resource_set is None:
            return path
        rset = from_resource.resource_set
        for key, value in rset.uri_mapper.items():
            if path.startswith(key):
                return path.replace(key, value)
        return path


class URIConverter(object):
    @classmethod
    def convert(cls, uri, resource_set=None):
        iter_from = global_uri_converter
        if resource_set:
            iter_from = chain(resource_set.uri_converter, global_uri_converter)

        for converter in iter_from:
            if converter.can_handle(uri):
                return converter.convert(uri)
        return uri


class AbstractURIConverter(object):
    @staticmethod
    @abstractmethod
    def can_handle(uri):
        raise NotImplementedError("can_handle(uri) should be implemented in "
                                  "its subclass")

    @staticmethod
    @abstractmethod
    def convert(uri):
        raise NotImplementedError("convert(uri) should be implemented in its "
                                  "subclass")


class HttpURIConverter(AbstractURIConverter):
    @staticmethod
    def can_handle(uri):
        return uri.protocol == 'http' or uri.protocol == 'https'

    @staticmethod
    def convert(uri):
        return HttpURI(uri.plain)


class LocalMetamodelDecoder(object):
    @staticmethod
    def can_resolve(path, from_resource=None):
        if from_resource is None or from_resource.resource_set is None:
            return False
        rset = from_resource.resource_set
        return MetamodelDecoder.can_resolve(path, rset.metamodel_registry)

    @staticmethod
    def resolve(path, from_resource=None):
        rset = from_resource.resource_set
        path = URIMapper.translate(path, from_resource)
        return MetamodelDecoder.resolve(path, rset.metamodel_registry)


class Resource(object):
    decoders = [LocalMetamodelDecoder, Global_URI_decoder]

    def __init__(self, uri=None, use_uuid=False):
        self.uuid_dict = {}
        self.use_uuid = use_uuid
        self.prefixes = {}
        self._uri = uri
        self.resource_set = None
        self.decoders = list(Resource.decoders)
        self.contents = []
        self.listeners = []
        self._eternal_listener = []
        self._resolve_mem = {}
        # self._feature_cache = {}
        self.cache_enabled = False

    @property
    def uri(self):
        return self._uri

    @uri.setter
    def uri(self, value):
        uri = value
        if isinstance(value, str):
            uri = URIConverter.convert(URI(value))
        if self.resource_set:
            old_uri = self._uri.normalize()
            resources = self.resource_set.resources
            old_resource = resources[old_uri]
            del resources[old_uri]
            resources[uri.normalize()] = old_resource
        self._uri = uri

    def resolve(self, fragment, resource=None):
        fragment = self.normalize(fragment)
        if fragment in self._resolve_mem:
            return self._resolve_mem[fragment]
        if self.use_uuid:
            with ignored(KeyError):
                frag = fragment[1:] if fragment.startswith('#') \
                                    else fragment
                frag = frag[2:] if frag.startswith('//') else frag
                return self.uuid_dict[frag]
        result = None
        root_number, fragment = self.extract_rootnum_and_frag(fragment)
        root = self.contents[root_number]
        result = self._navigate_from(fragment, root)
        if self.cache_enabled and result:
            self._resolve_mem[fragment] = result
        return result

    def resolve_object(self, path):
        decoder = next((x for x in self.decoders
                        if x.can_resolve(path, self)), None)
        if decoder:
            return decoder.resolve(path, self)
        newpath = URIMapper.translate(path, self)
        decoder = self._get_href_decoder(newpath, path)
        return decoder.resolve(newpath, self)

    @staticmethod
    def extract_rootnum_and_frag(fragment):
        if re.match(r'^/\d+.*', fragment):
            fragment = fragment[1:]
            if '/' in fragment:
                index = fragment.index('/')
            else:
                index = len(fragment)
            root_number = fragment[:index]
            fragment = fragment[index:]
            return (int(root_number), fragment)
        else:
            return (0, fragment)

    def prefix2epackage(self, prefix):
        nsURI = None
        try:
            nsURI = self.prefixes[prefix]
        except KeyError:
            return None
        try:
            return self.resource_set.metamodel_registry[nsURI]
        except Exception:
            return global_registry.get(nsURI)

    def get_metamodel(self, nsuri):
        try:
            if self.resource_set:
                return self.resource_set.metamodel_registry[nsuri]
            else:
                return global_registry[nsuri]
        except KeyError:
            raise KeyError(f'Unknown metamodel with uri: {nsuri}')

    @staticmethod
    def normalize(fragment):
        return fragment.split()[-1:][0] if ' ' in fragment else fragment

    def _is_external(self, path):
        path = self.normalize(path)
        uri, fragment = (path.rsplit('#', maxsplit=1)
                         if '#' in path else (None, path))
        return uri, fragment

    def _get_href_decoder(self, path, original_path):
        decoder = next((x for x in self.decoders
                        if x.can_resolve(path, self)), None)
        uri, _ = self._is_external(path)
        original_uri, _ = self._is_external(original_path)
        if not decoder and uri:
            decoder = self._try_resource_autoload(uri, original_uri)
        return decoder if decoder else self

    def _try_resource_autoload(self, uri, original_uri):
        try:
            rset = self.resource_set
            tmp_uri = URI(self.uri.apply_relative_from_me(uri))
            external_uri = URIConverter.convert(tmp_uri, self.resource_set)
            norm_plain = self.uri.apply_relative_from_me(external_uri.plain)
            external_uri.plain = norm_plain
            external_uri._split()
            resource = rset.get_resource(external_uri)
            if external_uri.plain != original_uri:
                rset.resources[original_uri] = resource
            return rset
        except Exception as e:
            raise TypeError(f'Resource "{uri}" cannot be resolved '
                            f'problem with "{e}"')

    @staticmethod
    def is_fragment_uuid(fragment):
        return fragment and fragment[0] != '/'

    @classmethod
    def _navigate_from(cls, path, start_obj):
        if '#' in path[:1]:
            path = path[1:]
        if cls.is_fragment_uuid(path) and start_obj.eResource:
            return start_obj.eResource.uuid_dict[path]

        features = [x for x in path.split('/') if x]
        feat_info = [x.split('.') for x in features]
        obj = start_obj
        annot_content = False
        for feat in feat_info:
            key, index = feat if len(feat) > 1 else (feat[0], None)
            if key.startswith('@'):
                tmp_obj = obj.__getattribute__(key[1:])
                try:
                    obj = tmp_obj[int(index)] if index else tmp_obj
                except IndexError:
                    raise ValueError('Index in path is not the collection,'
                                     ' broken proxy?')
                except ValueError:
                    # If index is not numeric it may be given as a name.
                    if index:
                        obj = tmp_obj.select(lambda x: x.name == index)[0]
            elif key.startswith('%'):
                key = key[1:-1]
                obj = obj.eAnnotations.select(lambda x: x.source == key)[0]
                annot_content = True
            elif annot_content:
                annot_content = False
                obj = obj.contents.select(lambda x: x.name == key)[0]
            else:
                with ignored(Exception):
                    subpack = next((p for p in obj.eSubpackages
                                    if p.name == key),
                                   None)
                    if subpack:
                        obj = subpack
                        continue
                try:
                    obj = obj.getEClassifier(key)
                except AttributeError:
                    obj = next((c for c in obj.eContents
                                if hasattr(c, 'name') and c.name == key),
                               None)
        return obj

    @staticmethod
    def get_id_attribute(eclass):
        for attribute in eclass.eAllAttributes():
            id_attr = attribute.__dict__.get('iD', False)
            try:
                res = id_attr._get()
            except Exception:
                res = id_attr
            if res:
                return attribute

    # Refactor me
    def _build_path_from(self, obj):
        if isinstance(obj, type):
            obj = obj.eClass

        # if isinstance(obj, Ecore.EProxy) and not obj.resolved:
        if not getattr(obj, 'resolved', True):
            return (obj._proxy_path, True)

        if obj.eResource != self:
            eclass = obj.eClass
            prefix = eclass.ePackage.nsPrefix
            _type = f'{prefix}:{eclass.name}'
            uri_fragment = obj.eURIFragment()
            crossref = False
            if obj.eResource:
                uri = self.uri.relative_from_me(obj.eResource.uri)
                crossref = True
                if obj.eResource.use_uuid:
                    self._assign_uuid(obj)
                    uri_fragment = obj._internal_id
                else:
                    id_attribute = self.get_id_attribute(eclass)
                    if id_attribute:
                        id_value = obj.eGet(id_attribute)
                        # id attributes shall not be used if the value is unset
                        if id_value:
                            uri_fragment = id_value
            else:
                uri = ''
                root = obj.eRoot()
                mm_registry = None
                if self.resource_set:
                    mm_registry = self.resource_set.metamodel_registry
                else:
                    mm_registry = global_registry
                for reguri, value in mm_registry.items():
                    if value is root:
                        uri = reguri
                        break
                else:
                    return '', False
            if not uri_fragment.startswith('#'):
                uri_fragment = '#' + uri_fragment
            if crossref:
                return (f'{uri}{uri_fragment}', True)
            else:
                return (f'{_type} {uri}{uri_fragment}', False)
        if self.use_uuid:
            self._assign_uuid(obj)
            return (obj._internal_id, False)
        id_attribute = self.get_id_attribute(obj.eClass)
        if id_attribute:
            etype = id_attribute._eType
            id_att_value = obj.eGet(id_attribute)
            # the check for ' ' prevents malformed ids to used as references
            if (id_att_value is not None) and (' ' not in id_att_value):
                return (etype.to_string(id_att_value), False)
        return (obj.eURIFragment(), False)

    @staticmethod
    def _assign_uuid(obj):
        # sets an uuid if the resource should deal with
        # and obj has none yet (addition to the resource for example)
        if not obj._internal_id:
            uuid = str(uuid4())
            obj._internal_id = uuid

    def append(self, root):
        if not isinstance(root, Ecore.EObject):
            raise ValueError('The resource requires an EObject type, '
                             f'but received {type(root)} instead.')
        self.contents.append(root)
        root._eresource = self
        if root._container is not None:
            container = root._container
            feature = root._containment_feature
            if feature.many:
                container.eGet(feature).remove(root)
            else:
                container.eSet(feature, None)

    def remove(self, root):
        self.contents.remove(root)
        root._eresource = None

    def open_out_stream(self, other=None):
        if other and not isinstance(other, URI):
            other = URI(other)
        return (other.create_outstream() if other
                else self.uri.create_outstream())

    def extend(self, values):
        append = self.append
        for x in values:
            append(x)

    @lru_cache()
    def _find_feature(self, eclass, name):
        return eclass.findEStructuralFeature(name)
        # fname = f'{eclass.name}#{name}'
        # try:
        #     return self._feature_cache[fname]
        # except KeyError:
        #     feature = eclass.findEStructuralFeature(name)
        #     self._feature_cache[fname] = feature
        #     return feature
