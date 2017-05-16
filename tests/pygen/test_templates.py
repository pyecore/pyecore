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
    cls1.eStructuralFeatures.append(EReference('b', cls2))
    cls2.eStructuralFeatures.append(EReference('a', cls1, eOpposite=cls1.findEStructuralFeature('b')))
    rootpkg.eClassifiers.append(cls1)
    rootpkg.eSubpackages.append(subpkg)
    subpkg.eClassifiers.append(cls2)

    mm = generate_meta_model(rootpkg, pygen_output_dir)

    assert mm.name == rootpkg.name

    generated_A = mm.getEClassifier('A')
    assert generated_A

    generated_subpkg = mm.eSubpackages[0]
    assert generated_subpkg
    assert generated_subpkg.name == 'subpkg'

    generated_B = generated_subpkg.getEClassifier('B')
    assert generated_B

    a = generated_A()
    b = generated_B()
    a.b = b

    assert b.a is a
