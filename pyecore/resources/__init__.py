from .resource import ResourceSet, Resource, URI, global_registry
from . import xmi
from .. import ecore as Ecore

# Register basic resource factory
ResourceSet.resource_factory = {'xmi': lambda uri: xmi.XMIResource(uri),
                                'ecore': lambda uri: xmi.XMIResource(uri),
                                '*': lambda uri: xmi.XMIResource(uri)}

global_registry[Ecore.nsURI] = Ecore

ecore_resource = Resource(uri=Ecore.nsURI)
ecore_resource.append(Ecore.eClass)


__all__ = ['ResourceSet', 'Resource', 'URI', 'global_registry']
