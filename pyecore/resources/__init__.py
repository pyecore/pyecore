from .resource import ResourceSet, Resource, URI, global_registry
from . import xmi


# Register basic resource factory
ResourceSet.resource_factory = {'xmi': lambda uri: xmi.XMIResource(uri),
                                'ecore': lambda uri: xmi.XMIResource(uri),
                                '*': lambda uri: xmi.XMIResource(uri)}

__all__ = ['ResourceSet', 'Resource', 'URI', 'global_registry']
