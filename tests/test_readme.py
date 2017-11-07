import pytest
from pyecore.ecore import *


def test_intro():
    A = EClass('A')  # We create metaclass named 'A'
    A.eStructuralFeatures.append(EAttribute('myname', EString,
                                            default_value='new_name'))
    a1 = A()  # We create an instance
    assert a1.myname == 'new_name'

    a1.myname = 'a_instance'
    assert a1.myname == 'a_instance'
    assert isinstance(a1, EObject)

    assert a1.eClass is A
    assert a1.eClass.eClass is EClass.eClass
    assert a1.eClass.eClass is a1.eClass.eClass.eClass
    assert a1.eClass.eStructuralFeatures
    assert a1.eClass.eStructuralFeatures[0].name == 'myname'
    assert a1.eClass.eStructuralFeatures[0].eClass is EAttribute.eClass
    assert a1.__getattribute__('myname') == 'a_instance'

    a1.__setattr__('myname', 'reflexive')
    assert a1.__getattribute__('myname') == 'reflexive'

    a1.eSet('myname', 'newname')
    assert a1.eGet('myname') == 'newname'

    with pytest.raises(BadValueError):
        a1.myname = 1


def test_instance_abstract_intro():
    MyMetaclass = EClass('MyMetaclass')
    instance1 = MyMetaclass()
    instance2 = MyMetaclass()
    assert instance1 is not instance2

    assert instance1.eClass.eAttributes == []
    MyMetaclass.eStructuralFeatures.append(EAttribute('name', EString))
    assert instance1.eClass.eAttributes != []
    assert instance1.name is None

    instance1.name = 'mystuff'
    assert instance1.name == 'mystuff'

    instance3 = MyMetaclass(name='myname')
    assert instance3.name == 'myname'
