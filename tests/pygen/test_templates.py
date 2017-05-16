"""Tests for the various features from the code generation templates."""
import importlib

from pyecore.ecore import EPackage, EClass, EReference
from pygen.ecore import EcoreGenerator


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


def test_top_level_package_with_subpackages(pygen_output_dir):
    rootpkg = EPackage('rootpkg')
    subpkg = EPackage('subpkg')
    cls1 = EClass('A')
    cls2 = EClass('B')
    cls2.eStructuralFeatures.append(EReference('b', cls2))
    subpkg.eClassifiers.extend((cls1, cls2))
    rootpkg.eSubpackages.append(subpkg)

    mm = generate_meta_model(rootpkg, pygen_output_dir)