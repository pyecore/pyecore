from uuid import uuid4
import urllib.request
import pyecore.ecore as Ecore

global_registry = {}


class ResourceSet(object):
    def __init__(self):
        self.resources = {}
        self.metamodel_registry = {}
        self.resource_factory = dict(ResourceSet.resource_factory)

    def create_resource(self, uri):
        if isinstance(uri, str):
            uri = URI(uri)
        try:
            resource = self.resource_factory[uri.extension](uri)
        except KeyError:
            resource = self.resource_factory['*'](uri)
        self.resources[uri._uri] = resource
        resource._resourceset = self
        resource._decoders.insert(0, self)
        return resource

    def get_resource(self, uri):
        resource = self.create_resource(uri)
        resource.load()
        return resource

    def can_resolve(self, uri_path):
        uri_path = Resource.normalize(uri_path)
        fragment = uri_path.split('#')
        if len(fragment) == 2:
            uri, fragment = fragment
        else:
            return False
        return uri in self.resources

    def resolve(self, uri):
        path = Resource.normalize(uri)
        uri, fragment = path.split('#')
        epackage = self.resources[uri]
        if isinstance(epackage, Resource):
            epackage = epackage.contents[0]
        return Resource._navigate_from(fragment, epackage)


class URI(object):
    def __init__(self, uri):
        if uri is None:
            raise TypeError('URI cannot be None')
        self._uri = uri
        self._split()
        self.__stream = None

    def _split(self):
        if '://' in self._uri:
            self._protocol, rest = self._uri.split('://')
        else:
            self._protocol, rest = None, self._uri
        if '.' in rest:
            self._extension = rest.split('.')[-1:][0]
        else:
            self._extension = None

    @property
    def protocol(self):
        return self._protocol

    @property
    def extension(self):
        return self._extension

    @property
    def plain(self):
        return self._uri

    def create_instream(self):
        self.__stream = open(self.plain, 'rb')
        return self.__stream

    def close_stream(self):
        if self.__stream:
            self.__stream.close()

    def create_outstream(self):
        self.__stream = open(self.plain, 'wb')
        return self.__stream


class HttpURI(URI):
    def __init__(self, uri):
        super().__init__(uri)

    def create_instream(self):
        self.__stream = urllib.request.urlopen(self.plain)
        return self.__stream

    def create_outstream(self):
        raise NotImplementedError('Cannot create an outstream for HttpURI')


# Not yet implementedn will return a kind of proxy
class File_URI_decoder(object):
    def can_resolve(path):
        return path.startswith('file://') or path.startswith('.')

    def resolve(path):
        pass


class Global_URI_decoder(object):
    def can_resolve(path):
        path = Resource.normalize(path)
        fragment = path.split('#')
        if len(fragment) == 2:
            uri, fragment = fragment
        else:
            uri = None
        return uri in global_registry

    def resolve(path):
        path = Resource.normalize(path)
        uri, fragment = path.split('#')
        epackage = global_registry[uri]
        return Resource._navigate_from(fragment, epackage)


class Resource(object):
    _decoders = [Global_URI_decoder, File_URI_decoder]

    def __init__(self, uri=None, use_uuid=False):
        self.uuid_dict = {}
        self._use_uuid = use_uuid
        self.prefixes = {}
        self._resourceset = None
        self._uri = uri
        self._decoders = list(Resource._decoders)
        self._contents = []

    @property
    def uri(self):
        return self._uri

    @property
    def resource_set(self):
        return self._resourceset

    @property
    def contents(self):
        return self._contents

    def resolve(self, fragment):
        raise NotImplemented('resolve method must be implemented')

    def prefix2epackage(self, prefix):
        try:
            return self.resource_set.metamodel_registry[self.prefixes[prefix]]
        except Exception:
            try:
                return global_registry[self.prefixes[prefix]]
            except Exception:
                return None

    def get_metamodel(self, nsuri):
        if self.resource_set:
            try:
                return self.resource_set.metamodel_registry[nsuri]
            except KeyError:
                pass
            try:
                return global_registry[nsuri]
            except KeyError:
                raise KeyError('Unknown metamodel with uri: {0}'.format(nsuri))

    def normalize(fragment):
        return fragment.split()[-1:][0] if ' ' in fragment else fragment

    def _get_decoder(self, path):
        decoder = next((x for x in self._decoders if x.can_resolve(path)),
                       None)
        return decoder if decoder else self

    def _navigate_from(path, start_obj):
        if '#' in path[:1]:
            path = path[1:]
        features = list(filter(None, path.split('/')))
        feat_info = [x.split('.') for x in features]
        obj = start_obj
        annot_content = False
        for feat in feat_info:
            key, index = feat if len(feat) > 1 else (feat[0], None)
            if key.startswith('@'):
                tmp_obj = obj.__getattribute__(key[1:])
                obj = tmp_obj[int(index)] if index else tmp_obj
            elif key.startswith('%'):
                key = key[1:-1]
                obj = obj.eAnnotations.select(lambda x: x.source == key)[0]
                annot_content = True
            elif annot_content:
                annot_content = False
                obj = obj.contents.select(lambda x: x.name == key)[0]
            else:
                try:
                    subpack = next((p for p in obj.eSubpackages
                                    if p.name == key),
                                   None)
                    if subpack:
                        obj = subpack
                        continue
                except Exception:
                    pass
                try:
                    obj = obj.getEClassifier(key)
                except AttributeError:
                    feat = obj.findEStructuralFeature(key)
                    if not feat:
                        obj = obj.findEOperation(key)
                    else:
                        obj = feat
        return obj

    def _build_path_from(self, obj):
        if obj.eResource != self:
            eclass = obj.eClass
            prefix = eclass.ePackage.nsPrefix
            _type = '{0}:{1}'.format(prefix, eclass.name)
            uri_fragment = obj.eURIFragment()
            if obj.eResource:
                uri = obj.eResource.uri.plain
            else:
                uri = ''
                root = obj.eRoot()
                for reguri, value in global_registry.items():
                    if value is root:
                        uri = reguri
                        break
                if not uri:
                    for reguri, value in global_registry.items():
                        if value is root:
                            uri = reguri
                            break
            if not uri_fragment.startswith('#'):
                uri_fragment = '#' + uri_fragment
            return '{0} {1}{2}'.format(_type, uri, uri_fragment)
        if self._use_uuid:
            self._assign_uuid(obj)
            return obj._xmiid
        return obj.eURIFragment()

    def _assign_uuid(self, obj):
        # sets an uuid if the resource should deal with
        # and obj has none yet (addition to the resource for example)
        if not obj._xmiid:
            uuid = str(uuid4())
            self.uuid_dict[uuid] = obj
            obj._xmiid = uuid

    def append(self, root):
        if not isinstance(root, Ecore.EObject):
            raise ValueError('The resource requires an EObject type, '
                             'but received {0} instead.'.format(type(root)))
        self._contents.append(root)
        for eobject in root.eAllContents():
            eobject._eresource = self

    def extend(self, values):
        map(self.append, values)
