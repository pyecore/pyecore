import pytest
from pyecore.ecore import *
from pyecore.commands import *
from pyecore.resources import URI, ResourceSet
from os import path


def test_editing_domain_create_resource():
    domain = EditingDomain()
    resource = domain.create_resource(URI('http://logical'))
    assert resource.contents == []


def test_editing_domain_load_resource():
    ecore_file = path.join('tests', 'xmi', 'xmi-tests', 'My.ecore')

    domain = EditingDomain()
    resource = domain.load_resource(URI(ecore_file))
    assert resource.contents

    root = resource.contents[0]
    assert isinstance(root, EPackage)


def test_editing_domain_execute_command_bad_eding_domain():
    ecore_file = path.join('tests', 'xmi', 'xmi-tests', 'My.ecore')

    resource = ResourceSet().get_resource(URI(ecore_file))
    root = resource.contents[0]

    cmd = Set(root, 'name', 'new_name')
    domain = EditingDomain()
    with pytest.raises(ValueError):
        domain.execute(cmd)


def test_editing_domain_execute_command():
    ecore_file = path.join('tests', 'xmi', 'xmi-tests', 'My.ecore')
    domain = EditingDomain()
    resource = domain.load_resource(URI(ecore_file))
    root = resource.contents[0]

    cmd = Set(root, 'name', 'new_name')
    domain.execute(cmd)
    assert root.name == 'new_name'


def test_editing_domain_execute_command_undo_redo():
    ecore_file = path.join('tests', 'xmi', 'xmi-tests', 'My.ecore')
    domain = EditingDomain()
    resource = domain.load_resource(URI(ecore_file))
    root = resource.contents[0]

    current_name = root.name

    cmd = Set(root, 'name', 'new_name')
    domain.execute(cmd)
    assert root.name == 'new_name'

    domain.undo()
    assert root.name == current_name

    domain.redo()
    assert root.name == 'new_name'
