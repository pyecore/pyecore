import pytest
import pyecore.ecore as Ecore
from pyecore.ecore import *
from pyecore.resources import *
from pyecore.resources.resource import Global_URI_decoder, File_URI_decoder


def test_init_globalregistry():
    assert global_registry
    assert global_registry[Ecore.nsURI]


def test_resourceset_defaut_decoders():
    assert 'xmi' in ResourceSet.resource_factory
    assert 'ecore' in ResourceSet.resource_factory
    assert '*' in ResourceSet.resource_factory


def test_uri_empty():
    uri = URI('')
    assert uri.protocol is None
    assert uri.extension is None
    assert uri.plain == ''


def test_uri_none():
    with pytest.raises(TypeError):
        URI(None)


def test_uri_simple():
    uri = URI('http://test.ecore')
    assert uri.protocol == 'http'
    assert uri.extension == 'ecore'
    assert uri.plain == 'http://test.ecore'


def test_uri_noextension():
    uri = URI('http://test')
    assert uri.protocol == 'http'
    assert uri.extension is None
    assert uri.plain == 'http://test'


def test_uri_noprotocol():
    uri = URI('test.ecore')
    assert uri.protocol is None
    assert uri.extension == 'ecore'
    assert uri.plain == 'test.ecore'


def test_uri_noprotocol_noextension():
    uri = URI('test')
    assert uri.protocol is None
    assert uri.extension is None
    assert uri.plain == 'test'


def test_resourceset_default_decoders():
    rset = ResourceSet()
    assert 'xmi' in rset.resource_factory
    assert 'ecore' in rset.resource_factory
    assert '*' in rset.resource_factory
    assert rset.resource_factory is not ResourceSet.resource_factory


def test_resourceset_createresource_simple():
    rset = ResourceSet()
    resource = rset.create_resource(URI('simpleuri'))
    assert 'simpleuri' in rset.resources
    assert rset.resources['simpleuri'] is resource
    assert rset in resource._decoders
    assert isinstance(resource, rset.resource_factory['*']('').__class__)


def test_resourceset_createresource_ecore():
    rset = ResourceSet()
    resource = rset.create_resource(URI('simple.ecore'))
    assert 'simple.ecore' in rset.resources
    assert rset.resources['simple.ecore'] is resource
    assert rset in resource._decoders
    assert isinstance(resource, rset.resource_factory['ecore']('').__class__)


def test_resourceset_createresource_xmi():
    rset = ResourceSet()
    resource = rset.create_resource(URI('simple.xmi'))
    assert 'simple.xmi' in rset.resources
    assert rset.resources['simple.xmi'] is resource
    assert rset in resource._decoders
    assert isinstance(resource, rset.resource_factory['xmi']('').__class__)


def test_resourceset_canresolve():
    rset = ResourceSet()
    assert rset.can_resolve('http://simple.ecore#//test') is False
    rset.create_resource(URI('http://simple.ecore'))
    assert rset.can_resolve('http://simple.ecore#//test') is True


def test_globaluridecoder():
    assert Global_URI_decoder.can_resolve('http://simple.ecore#//test') is False
    rset = ResourceSet()
    resource = rset.create_resource('http://simple.ecore')
    global_registry['http://simple.ecore'] = resource
    assert Global_URI_decoder.can_resolve('http://simple.ecore#//test') is True


def test_fileuridecoder():
    assert File_URI_decoder.can_resolve('file://simple.ecore#//test') is True
