"""Tests for the various features from the code generation templates."""
import importlib
import os
import shutil

import pytest
import sys

from pyecore.ecore import EPackage
from pyecore.resources import ResourceSet, URI
from pygen.ecore import EcoreGenerator


@pytest.fixture('module', autouse=True)
def cwd_module_dir():
    # change cwd to this module's directory:
    cwd = os.getcwd()
    os.chdir(os.path.dirname(__file__))
    yield

    # reset after module goes out of scope:
    os.chdir(cwd)


@pytest.fixture
def pygen_output_dir():
    path = os.path.join('output', 'template_features')
    shutil.rmtree(path, ignore_errors=True)
    original_sys_path = sys.path
    sys.path.append(path)
    yield path
    sys.path.remove(path)
    #shutil.rmtree(path, ignore_errors=False)


def generate_meta_model(model, output_dir):
    generator = EcoreGenerator()
    generator.generate(model, output_dir)
    return importlib.import_module(model.name)


def test_empty_package(pygen_output_dir):
    package = EPackage('empty')
    mm = generate_meta_model(package, pygen_output_dir)

    assert mm
    assert mm.name == 'empty'
    assert not mm.nsURI
    assert not mm.nsPrefix
    assert not mm.eClassifiers

    package.name = 'empty2'
    package.nsURI = 'http://xyz.org'
    package.nsPrefix = 'p'
    mm = generate_meta_model(package, pygen_output_dir)
    assert mm.nsURI == 'http://xyz.org'
    assert mm.nsPrefix == 'p'
