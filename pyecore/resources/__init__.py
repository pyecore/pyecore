from .resource import ResourceSet, Resource, URI, global_registry, \
                      global_uri_mapper
from . import xmi
from .. import ecore as Ecore

# Register basic resource factory
ResourceSet.resource_factory = {'xmi': xmi.XMIResource,
                                'ecore': xmi.XMIResource,
                                '*': xmi.XMIResource}

global_registry[Ecore.nsURI] = Ecore

__all__ = ['ResourceSet', 'Resource', 'URI', 'global_registry',
           'global_uri_mapper']
