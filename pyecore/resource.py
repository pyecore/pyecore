class ResourceSet(object):
    def __init__(self):
        self.metamodel_registry = {}
        self.resources = {}

    def create_resource(uri):
        pass


class URI(object):
    def __init__(self, uri):
        self._uri = uri
        self._split()

    def _split(self):
        if '://' in self._uri:
            self._protocol, rest = self._uri.split('://')
        else:
            self._protocol, rest = None, self._uri
        self._extension = rest.split('.')[-1:] if rest else None

    @property
    def protocol(self):
        return self._protocol

    @property
    def extension(self):
        return self._extension


global_registry = {}
