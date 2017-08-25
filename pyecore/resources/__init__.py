from .resource import ResourceSet, Resource, URI, global_registry
from . import xmi
from .. import ecore as Ecore
from .. import type as XMLType


# Register basic resource factory
ResourceSet.resource_factory = {'xmi': lambda uri: xmi.XMIResource(uri),
                                'ecore': lambda uri: xmi.XMIResource(uri),
                                '*': lambda uri: xmi.XMIResource(uri)}

global_registry[Ecore.nsURI] = Ecore
global_registry[XMLType.nsURI] = XMLType

__all__ = ['ResourceSet', 'Resource', 'URI', 'global_registry']
