"""Copy of the original static library module tests."""
import os
import shutil

import pytest
import sys

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


@pytest.fixture(scope='module')
def pygen_output_dir():
    path = os.path.join('output', 'pygen2')
    shutil.rmtree(path, ignore_errors=True)
    original_sys_path = sys.path
    sys.path.append(path)
    yield path
    sys.path.remove(path)
    #shutil.rmtree(path, ignore_errors=False)


@pytest.fixture(scope='module')
def generated_library(pygen_output_dir):
    rset = ResourceSet()
    resource = rset.get_resource(URI('../../examples/library.ecore'))
    library_model = resource.contents[0]
    rset.metamodel_registry[library_model.nsURI] = library_model
    generator = EcoreGenerator()
    generator.generate(library_model, pygen_output_dir)
    import library as library_gen
    return library_gen


def test_library_eroot_generated(generated_library):
    lib = generated_library.Library()
    smith = generated_library.Writer()
    lib.writers.append(smith)
    assert smith.eContainer() is lib
    assert smith.eRoot() is lib
    assert generated_library.Library.eClass.eRoot() is generated_library.eClass
