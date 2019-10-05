from .resource import ResourceSet, Resource, URI, global_registry, \
                      global_uri_mapper, global_uri_converter, \
                      HttpURIConverter, AbstractURIConverter
from . import xmi
from .. import ecore as Ecore

# Register basic resource factory
ResourceSet.resource_factory = {'xmi': xmi.XMIResource,
                                'ecore': xmi.XMIResource,
                                '*': xmi.XMIResource}

global_registry[Ecore.nsURI] = Ecore

# Register HTTPURIConverter
global_uri_converter.append(HttpURIConverter)

__all__ = ['ResourceSet', 'Resource', 'URI', 'global_registry',
           'global_uri_mapper', 'global_uri_converter', 'AbstractURIConverter']
