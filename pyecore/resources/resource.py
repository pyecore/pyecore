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
        return Resource._navigate_from(fragment, epackage)


class URI(object):
    def __init__(self, uri):
        if uri is None:
            raise TypeError('URI cannot be None')
        self._uri = uri
        self._split()

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
        try:
            global_registry[uri]
            return True
        except KeyError:
            return False

    def resolve(path):
        path = Resource.normalize(path)
        uri, fragment = path.split('#')
        epackage = global_registry[uri]
        return Resource._navigate_from(fragment, epackage)


class Resource(object):
    _decoders = [Global_URI_decoder, File_URI_decoder]

    def __init__(self, uri=None):
        self.uuid_dict = {}
        self._use_uuid = False
        self.prefixes = {}
        self._resourceset = None
        self._uri = uri
        self._decoders = list(Resource._decoders)

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
        return global_registry[nsuri]

    def normalize(fragment):
        return fragment.split()[-1:][0] if ' ' in fragment else fragment

    def _get_decoder(self, path):
        decoder = next((x for x in self._decoders if x.can_resolve(path)),
                       None)
        return decoder if decoder else self

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
