import pytest

from pyecore.ecore import EObject, EcoreUtils, EPackage, EClass, EEnum
from pygen.ecore import ModelTypeMixin


def test__model_type_mixin__filtered_elements():
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

    mixin = ModelTypeMixin()

    mixin.element_type = EClass
    assert set(mixin.filtered_elements(package)) == {class1, class2}

    mixin.element_type = EEnum
    assert set(mixin.filtered_elements(package)) == {enum}
