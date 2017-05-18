import os

import pytest

from pyecore.ecore import EPackage, EClass, EEnum
from pygen.ecore import EcoreTask, EcorePackageInitTask, EcorePackageModuleTask, EcoreGenerator


def test__ecore_task__filtered_elements():
    # prepare test model:
    # -------------------
    # ThePackage
    #   Class1
    #   SubPackage
    #     Class2
    #     MyEnum
    package = EPackage('ThePackage')
    class1 = EClass('Class1')
    class2 = EClass('Class2')
    enum = EEnum('MyEnum', literals=['A', 'B'])

    subpackage = EPackage('SubPackage')
    package.eSubpackages.append(subpackage)

    package.eClassifiers.append(class1)
    subpackage.eClassifiers.extend([class2, enum])

    task = EcoreTask()

    task.element_type = EPackage
    assert set(task.filtered_elements(package)) == {package, subpackage}

    task.element_type = EClass
    assert set(task.filtered_elements(package)) == {class1, class2}

    task.element_type = EEnum
    assert set(task.filtered_elements(package)) == {enum}


@pytest.fixture
def package_in_hierarchy():
    pkg1 = EPackage('pkg1')
    pkg2 = EPackage('pkg2')
    pkg3 = EPackage('pkg3')
    pkg1.eSubpackages.append(pkg2)
    pkg2.eSubpackages.append(pkg3)
    return pkg3


def test__ecore_package_init_task__path_for_element(package_in_hierarchy):
    path = EcorePackageInitTask().relative_path_for_element(package_in_hierarchy)
    assert path == os.path.join('pkg1', 'pkg2', 'pkg3', '__init__.py')


def test__ecore_package_module_task__path_for_element(package_in_hierarchy):
    path = EcorePackageModuleTask().relative_path_for_element(package_in_hierarchy)
    assert path == os.path.join('pkg1', 'pkg2', 'pkg3', 'pkg3.py')


def test__ecore_generator__filter_pyfqn(package_in_hierarchy):
    assert EcoreGenerator.filter_pyfqn(package_in_hierarchy) == 'pkg1.pkg2.pkg3'
    assert EcoreGenerator.filter_pyfqn(package_in_hierarchy, relative_to=1) == '.pkg2.pkg3'
    assert EcoreGenerator.filter_pyfqn(package_in_hierarchy, relative_to=2) == '.pkg3'
    assert EcoreGenerator.filter_pyfqn(package_in_hierarchy, relative_to=3) == '.'

    with pytest.raises(ValueError):
        assert EcoreGenerator.filter_pyfqn(package_in_hierarchy, relative_to=4) == '.'
