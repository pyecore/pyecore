"""Common fixtures and configurations for this test directory."""
import os
import shutil
import sys

import pytest


@pytest.fixture('module')
def cwd_module_dir():
    """Change current directory to this module's folder to access inputs and write outputs."""
    cwd = os.getcwd()
    os.chdir(os.path.dirname(__file__))
    yield
    os.chdir(cwd)


@pytest.fixture(scope='module')
def pygen_output_dir(cwd_module_dir):
    """Return an empty output directory, part of syspath to allow importing generated code."""
    path = 'output'
    shutil.rmtree(path, ignore_errors=True)
    original_sys_path = sys.path
    sys.path.append(path)
    yield path
    sys.path.remove(path)
    shutil.rmtree(path, ignore_errors=False)
