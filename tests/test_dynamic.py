import pytest
from datetime import datetime
from pyecore.ecore import *
import pyecore.ecore as ecore


def test_eclass_meta_attribute_access():
    assert isinstance(EClass.name, EAttribute)
    assert EClass.name.eType is EString


def test_ecore_bad_names():
    with pytest.raises(BadValueError):
        EParameter(name=33)
    with pytest.raises(BadValueError):
        EOperation(name=33)
    with pytest.raises(BadValueError):
        EClass(name=33)
    with pytest.raises(BadValueError):
        EAttribute(name=33)
    with pytest.raises(BadValueError):
        EReference(name=33)


def test_eclass_meta_reference_access():
    assert isinstance(EClass.eStructuralFeatures, EReference)
    assert EClass.eStructuralFeatures.eType is EStructuralFeature


def test_eclass_meta_eopposite_reference_access():
    assert isinstance(EReference.eOpposite_, EReference)
    assert EReference.eOpposite_.eType is EReference
    assert EReference.eOpposite_.name == 'eOpposite'


def test_create_dynamic_eclass():
    A = EClass('A')
    assert isinstance(A, EObject) and isinstance(A, EClass)
    assert A.eStructuralFeatures == []
    assert A.eReferences == []
    assert A.eAttributes == []
    assert A.eOperations == []
    assert A.eAllOperations() == set()
    assert A.eAllStructuralFeatures() == set()


def test_create_dynamic_eclass_urifragment():
    A = EClass('A')
    assert A.eURIFragment() == '#/'  # A is the root at this point
    pack = EPackage('pack')
    pack.eClassifiers.append(A)  # pack is the root now
    assert A.eURIFragment() == '#//A'


def test_create_dynamic_instance():
    A = EClass('A')
    instance = A()
    assert EcoreUtils.isinstance(instance, A)
    assert isinstance(instance, EObject)


def test_create_dynamic_instance_urifragment():
    A = EClass('A')
    instance = A()
    assert instance.eURIFragment() == '/'


def test_create_dynamic_simple_eattribute():
    A = EClass('A')
    A.eStructuralFeatures.append(EAttribute('name', EString))
    a = A()
    assert a.name is None
    a.name = 'new_name'
    assert a.name == 'new_name'


def test_create_dynamic_simple_eattribute_boolean():
    A = EClass('A')
    A.eStructuralFeatures.append(EAttribute('isStuff', EBoolean))
    a = A()
    assert a.isStuff is False
    a.isStuff = True
    assert a.isStuff is True


def test_create_dynamic_simple_eattribute_badvalue():
    A = EClass('A')
    A.eStructuralFeatures.append(EAttribute('name', EString))
    a = A()
    with pytest.raises(BadValueError):
        a.name = 42


def test_create_dynamic_access_badtype():
    A = EClass('A')
    a = A()
    with pytest.raises(AttributeError):
        a.name


def test_create_dynamic_many_eattribute():
    A = EClass('A')
    A.eStructuralFeatures.append(EAttribute('names', EString, upper=-1))
    a = A()
    assert a.names == []
    a.names.append('name1')
    a.names.append('name2')
    assert 'name1' in a.names and 'name2' in a.names


def test_create_dynamic_override_many_eattribute():
    A = EClass('A')
    A.eStructuralFeatures.append(EAttribute('names', EString, upper=-1))
    a = A()
    with pytest.raises(BadValueError):
        a.names = 'test'
    assert a.names == []


def test_create_dynamic_simple_ereference():
    A = EClass('A')
    B = EClass('B')
    A.eStructuralFeatures.append(EReference('tob', B))
    a1 = A()
    b1 = B()
    a1.tob = b1
    assert a1.tob is b1
    assert A.eStructuralFeatures[0].get_default_value() is None
    assert A.eStructuralFeatures[0] in A.eReferences
    assert A.eStructuralFeatures is not A.eReferences


def test_create_dynamic_simple_ereference_urifragment():
    A = EClass('A')
    B = EClass('B')
    A.eStructuralFeatures.append(EReference('tob', B, containment=True))
    a1 = A()
    b1 = B()
    a1.tob = b1
    assert b1.eURIFragment() == '//tob'


def test_create_dynamic_simple_ereference_wrongtype():
    A = EClass('A')
    B = EClass('B')
    A.eStructuralFeatures.append(EReference('tob', B))
    a1 = A()
    with pytest.raises(BadValueError):
        a1.tob = 3


def test_create_dynamic_simple_ereference_unset():
    A = EClass('A')
    B = EClass('B')
    A.eStructuralFeatures.append(EReference('tob', B))
    a1 = A()
    b1 = B()
    a1.tob = b1
    a1.tob = None
    assert a1.tob is None


def test_create_dynamic_many_ereference():
    A = EClass('A')
    B = EClass('B')
    A.eStructuralFeatures.append(EReference('tob', B, upper=-1))
    a1 = A()
    b1 = B()
    a1.tob.append(b1)
    assert a1.tob
    assert b1 in a1.tob
    assert len(a1.tob) == 1
    assert a1.tob.__repr__()


def test_create_dynamic_many_ereference_urifragment():
    A = EClass('A')
    B = EClass('B')
    A.eStructuralFeatures.append(EReference('tob', B, upper=-1, containment=True))
    a1 = A()
    b1 = B()
    a1.tob.append(b1)
    assert b1.eURIFragment() == '//@tob.0'


def test_create_dynamic_many_ereference_filter():
    A = EClass('A')
    B = EClass('B')
    A.eStructuralFeatures.append(EReference('b', B, upper=-1))
    a1 = A()
    b1 = B()
    a1.b.append(b1)
    result = a1.b.select(lambda x: x)
    assert result is not a1.b
    assert b1 in result


def test_create_dynamic_many_ereference_reject():
    A = EClass('A')
    B = EClass('B')
    A.eStructuralFeatures.append(EReference('b', B, upper=-1))
    a1 = A()
    b1 = B()
    a1.b.append(b1)
    result = a1.b.reject(lambda x: x)
    assert result is not a1.b
    assert b1 not in result and result == []


def test_create_dynamic_many_ereference_wrongtype():
    A = EClass('A')
    B = EClass('B')
    A.eStructuralFeatures.append(EReference('tob', B, upper=-1))
    a1 = A()
    with pytest.raises(BadValueError):
        a1.tob.append(3)


def test_create_dynamic_many_ereference_remove():
    A = EClass('A')
    B = EClass('B')
    A.eStructuralFeatures.append(EReference('tob', B, upper=-1))
    a1 = A()
    b1 = B()
    a1.tob.append(b1)
    a1.tob.remove(b1)
    assert a1.tob == []


def test_create_dynamic_ereference_one2one():
    A = EClass('A')
    B = EClass('B')
    A.eStructuralFeatures.append(EReference('b', B))
    B.eStructuralFeatures.append(EReference('a', A, eOpposite=A.eStructuralFeatures[0]))
    a1 = A()
    b1 = B()
    a1.b = b1
    assert a1.b is b1
    assert b1.a is a1


def test_create_dynamic_ereference_one2one_unset():
    A = EClass('A')
    B = EClass('B')
    A.eStructuralFeatures.append(EReference('b', B))
    B.eStructuralFeatures.append(EReference('a', A, eOpposite=A.eStructuralFeatures[0]))
    a1 = A()
    b1 = B()
    a1.b = b1
    assert a1.b is b1
    assert b1.a is a1
    a1.b = None
    assert a1.b is None
    assert b1.a is None


def test_create_dynamic_ereference_many2one():
    A = EClass('A')
    B = EClass('B')
    A.eStructuralFeatures.append(EReference('b', B, upper=-1))
    B.eStructuralFeatures.append(EReference('a', A, eOpposite=A.eStructuralFeatures[0]))
    a1 = A()
    b1 = B()
    a1.b.append(b1)
    assert b1 in a1.b and len(a1.b) == 1
    assert b1.a is a1


def test_create_dynamic_ereference_many2one_unset():
    A = EClass('A')
    B = EClass('B')
    A.eStructuralFeatures.append(EReference('b', B, upper=-1))
    B.eStructuralFeatures.append(EReference('a', A, eOpposite=A.eStructuralFeatures[0]))
    a1 = A()
    b1 = B()
    a1.b.append(b1)
    assert b1 in a1.b and len(a1.b) == 1
    assert b1.a is a1
    a1.b.remove(b1)
    assert b1 not in a1.b and a1.b == []
    assert b1.a is None


def test_create_dynamic_ereference_one2many():
    A = EClass('A')
    B = EClass('B')
    A.eStructuralFeatures.append(EReference('b', B))
    B.eStructuralFeatures.append(EReference('a', A, upper=-1, eOpposite=A.eStructuralFeatures[0]))
    a1 = A()
    b1 = B()
    a1.b = b1
    assert a1.b is b1
    assert a1 in b1.a and len(b1.a) == 1


def test_create_dynamic_ereference_one2many_unset():
    A = EClass('A')
    B = EClass('B')
    A.eStructuralFeatures.append(EReference('b', B))
    B.eStructuralFeatures.append(EReference('a', A, upper=-1, eOpposite=A.eStructuralFeatures[0]))
    a1 = A()
    b1 = B()
    a1.b = b1
    assert a1.b is b1
    assert a1 in b1.a and len(b1.a) == 1
    a1.b = None
    assert a1 not in b1.a and b1.a == []
    assert a1.b is None


def test_create_dynamic_ereference_many2many():
    A = EClass('A')
    B = EClass('B')
    A.eStructuralFeatures.append(EReference('b', B, upper=-1))
    B.eStructuralFeatures.append(EReference('a', A, upper=-1, eOpposite=A.eStructuralFeatures[0]))
    a1 = A()
    b1 = B()
    a1.b.append(b1)
    assert b1 in a1.b and len(a1.b) == 1
    assert a1 in b1.a and len(b1.a) == 1


def test_create_dynamic_ereference_many2many_unset():
    A = EClass('A')
    B = EClass('B')
    A.eStructuralFeatures.append(EReference('b', B, upper=-1))
    B.eStructuralFeatures.append(EReference('a', A, upper=-1, eOpposite=A.eStructuralFeatures[0]))
    a1 = A()
    b1 = B()
    a1.b.append(b1)
    assert b1 in a1.b
    assert a1 in b1.a
    a1.b.remove(b1)
    assert b1 not in a1.b and a1.b == []
    assert a1 not in b1.a and b1.a == []


def test_create_dynamic_inheritances():
    A = EClass('A')
    B = EClass('B', superclass=A)
    b1 = B()
    assert EcoreUtils.isinstance(b1, B)
    assert EcoreUtils.isinstance(b1, A)


def test_create_dynamic_multi_inheritances():
    A = EClass('A')
    B = EClass('B')
    C = EClass('C', superclass=(A, B))
    c1 = C()
    assert EcoreUtils.isinstance(c1, C)
    assert EcoreUtils.isinstance(c1, B)
    assert EcoreUtils.isinstance(c1, A)


def test_create_dynamic_abstract_eclass():
    A = EClass('A', abstract=True)
    with pytest.raises(TypeError):
        A()


def test_create_dynamic_subclass_from_abstract_eclass():
    A = EClass('A', abstract=True)
    B = EClass('B', superclass=A)
    b = B()
    assert EcoreUtils.isinstance(b, B)
    assert EcoreUtils.isinstance(b, A)


def test_create_dynamic_contaiment_many_ereferene():
    A = EClass('A')
    B = EClass('B')
    A.eStructuralFeatures.append(EReference('b', B, upper=-1, containment=True))
    a1 = A()
    b1 = B()
    a1.b.append(b1)
    assert b1.eContainer() is a1


def test_create_dynamic_contaiment_many_ereferene_unset():
    A = EClass('A')
    B = EClass('B')
    A.eStructuralFeatures.append(EReference('b', B, upper=-1, containment=True))
    a1 = A()
    b1 = B()
    a1.b.append(b1)
    assert b1.eContainer() is a1
    a1.b.remove(b1)
    assert b1.eContainer() is None


def test_create_dynamic_contaiment_single_ereferene():
    A = EClass('A')
    B = EClass('B')
    A.eStructuralFeatures.append(EReference('b', B, containment=True))
    a1 = A()
    b1 = B()
    a1.b = b1
    assert b1.eContainer() is a1


def test_create_dynamic_contaiment_getroot():
    A = EClass('A')
    B = EClass('B')
    A.eStructuralFeatures.append(EReference('b', B, containment=True))
    a1 = A()
    b1 = B()
    a1.b = b1
    assert EcoreUtils.get_root(b1) is a1
    assert EcoreUtils.get_root(None) is None
    assert b1.eRoot() is a1


def test_create_dynamic_contaiment_single_ereferene_unset():
    A = EClass('A')
    B = EClass('B')
    A.eStructuralFeatures.append(EReference('b', B, containment=True))
    a1 = A()
    b1 = B()
    a1.b = b1
    assert b1.eContainer() is a1
    a1.b = None
    assert b1.eContainer() is None


def test_create_dynamic_contaiment_containmentfeature():
    A = EClass('A')
    B = EClass('B')
    A.eStructuralFeatures.append(EReference('b', B, containment=True))
    a1 = A()
    b1 = B()
    a1.b = b1
    assert isinstance(b1.eContainmentFeature(), EReference)
    assert b1.eContainmentFeature() in A.eStructuralFeatures


def test_create_dynamic_contaiment_containmentfeature_unset():
    A = EClass('A')
    B = EClass('B')
    A.eStructuralFeatures.append(EReference('b', B, containment=True))
    a1 = A()
    b1 = B()
    a1.b = b1
    assert isinstance(b1.eContainmentFeature(), EReference)
    assert b1.eContainmentFeature() in A.eStructuralFeatures
    a1.b = None
    assert b1.eContainmentFeature() is None


def test_create_dynamic_contaiment_containmentfeature_many():
    A = EClass('A')
    B = EClass('B')
    A.eStructuralFeatures.append(EReference('b', B, containment=True, upper=-1))
    a1 = A()
    b1 = B()
    a1.b.append(b1)
    assert isinstance(b1.eContainmentFeature(), EReference)
    assert b1.eContainmentFeature() in A.eStructuralFeatures


def test_create_dynamic_contaiment_containmentfeature_many_unset():
    A = EClass('A')
    B = EClass('B')
    A.eStructuralFeatures.append(EReference('b', B, containment=True, upper=-1))
    a1 = A()
    b1 = B()
    a1.b.append(b1)
    assert isinstance(b1.eContainmentFeature(), EReference)
    assert b1.eContainmentFeature() in A.eStructuralFeatures
    a1.b.remove(b1)
    assert b1.eContainmentFeature() is None


def test_dynamic_extend_ecore():
    A = EClass('A')
    A.eSuperTypes.append(EModelElement.eClass)  # A now extends EModelElement
    a1 = A()
    assert a1.eAnnotations == []
    a1.eAnnotations.append(EAnnotation('test'))
    assert len(a1.eAnnotations) == 1
    a1.eAnnotations[0].details['new_value'] = True
    assert 'new_value' in a1.eAnnotations[0].details


def test_dynamic_crate_epackage():
    A = EClass('A')
    package = EPackage('testpack', nsURI='http://test/1.0', nsPrefix='test')
    package.eClassifiers.append(A)
    assert package.eClassifiers != []
    assert A in package.eClassifiers
    assert package.getEClassifier('A') is A


def test_create_dynamic_ereference_ord_nonuni():
    A = EClass('A')
    B = EClass('B')
    A.eStructuralFeatures.append(EReference('tob', B, unique=False, upper=-1))
    a1 = A()
    b1 = B()
    a1.tob.append(b1)
    assert isinstance(a1.tob, EList)
    assert b1 in a1.tob


def test_create_dynamic_ereference_nonord_uni():
    A = EClass('A')
    B = EClass('B')
    A.eStructuralFeatures.append(EReference('tob', B, unique=True, upper=-1, ordered=False))
    a1 = A()
    b1 = B()
    a1.tob.append(b1)
    assert isinstance(a1.tob, ESet)
    assert isinstance(a1.tob, EOrderedSet)
    assert b1 in a1.tob


def test_create_dynamic_ereference_nonord_nonuni():
    A = EClass('A')
    B = EClass('B')
    A.eStructuralFeatures.append(EReference('tob', B, unique=False, upper=-1, ordered=False))
    a1 = A()
    b1 = B()
    a1.tob.append(b1)
    assert isinstance(a1.tob, EBag)
    assert isinstance(a1.tob, EList)
    assert b1 in a1.tob
    assert a1.tob.__repr__()


def test_create_dynamic_ereference_elist_extend():
    A = EClass('A')
    B = EClass('B')
    A.eStructuralFeatures.append(EReference('tob', B, unique=False, upper=-1))
    a1 = A()
    b1 = B()
    b2 = B()
    assert isinstance(a1.tob, EList)
    a1.tob.extend([b1, b2])
    assert b1 in a1.tob
    assert b2 in a1.tob


def test_create_dynamic_ereference_elist_setitem():
    A = EClass('A')
    B = EClass('B')
    A.eStructuralFeatures.append(EReference('tob', B, unique=False, upper=-1))
    a1 = A()
    b1 = B()
    b2 = B()
    a1.tob.append(b1)
    a1.tob[0] = b2
    assert b1 not in a1.tob
    assert b2 in a1.tob


def test_create_dynamic_ereference_bounds():
    A = EClass('A')
    B = EClass('B')
    A.eStructuralFeatures.append(EReference('tob', B, unique=False, lower=2, upper=5, ordered=False))
    # assert A.eStructuralFeatures[0].lower == 2
    # assert A.eStructuralFeatures[0].upper == 5
    assert A.eStructuralFeatures[0].lowerBound == 2
    assert A.eStructuralFeatures[0].upperBound == 5


def test_create_simple_metamodel():
    ec = EClass('A')
    eat = EAttribute('eatt', eType=EString)
    ec.eStructuralFeatures.append(eat)
    pack = EPackage('epack')
    pack.eClassifiers.append(ec)
    assert ec in pack.eContents and eat not in pack.eContents
    assert ec in pack.eAllContents() and eat in pack.eAllContents()


# This test is a little bit special (not a real unit test)
def test_update_estructuralfeature_in_eclass():
    A = EClass('A')
    a = A()

    with pytest.raises(AttributeError):
        a.name

    A.eStructuralFeatures.append(EAttribute('name', EString))
    a.name  # We access the name
    assert a.__dict__['name'].owner is a


def test_get_eattribute():
    A = EClass('A')
    name = EAttribute('name', EString)
    A.eStructuralFeatures.append(name)
    eref = EReference('child', A, containment=True)
    A.eStructuralFeatures.append(eref)
    assert A.eAttributes
    assert len(A.eAttributes) == 1
    assert name in A.eAttributes


def test_get_ereferences():
    A = EClass('A')
    name = EAttribute('name', EString)
    A.eStructuralFeatures.append(name)
    eref = EReference('child', A, containment=True)
    A.eStructuralFeatures.append(eref)
    assert A.eReferences
    assert len(A.eReferences) == 1
    assert eref in A.eReferences


def test_eclass_emodelemenent_supertype():
    A = EClass('A', superclass=(EModelElement.eClass,))
    assert EModelElement.eAnnotations in A.eAllStructuralFeatures()
    a = A()
    assert a.eAnnotations == {}


def test_eclass_remove_estructuralfeature():
    A = EClass('A')
    name_feature = EAttribute('name', EString)
    A.eStructuralFeatures.append(name_feature)
    assert name_feature in A.eStructuralFeatures
    assert A.python_class.name is name_feature
    A.eStructuralFeatures.clear()
    assert name_feature not in A.eStructuralFeatures
    with pytest.raises(AttributeError):
        A.python_class.name


def test_eclass_remove_eoperation():
    A = EClass('A')
    operation = EOperation('testOperation')
    A.eOperations.append(operation)
    assert operation in A.eOperations
    assert A.python_class.testOperation is not None
    A.eOperations.clear()
    assert operation not in A.eOperations
    with pytest.raises(AttributeError):
        A.python_class.testOperation


def test_eclass_operations_methods():
    A = EClass('A')
    op1 = EOperation('operation1')
    A.eOperations.append(op1)
    B = EClass('B', superclass=(A,))
    op2 = EOperation('operation2')
    B.eOperations.append(op2)
    assert B.eAllOperations() == {op1, op2}

    assert B.findEOperation('operation1') is op1
    assert B.findEOperation('operation2') is op2
    assert A.findEOperation('operation2') is None


def test_eclass_simple_reference():
    A = EClass('A')
    B = EClass('B')
    A.eStructuralFeatures.append(EReference('tob', B, upper=1))
    a = A()
    assert a.tob is None


def test_eclass_multi_eattribute_once():
    A = EClass('A')
    x = EAttribute('x', EFeatureMapEntry)
    y = EAttribute('y', EFeatureMapEntry)
    A.eStructuralFeatures.extend([x, y])
    a = A()
    assert a.x == {}
    assert a.y == {}
    a.x['key'] = 33
    assert a.x == {'key': 33}
    assert a.y == {}


def test_eoperation_with_params():
    A = EClass('A')
    param1 = EParameter('p1', EString)
    param2 = EParameter('p2', A)
    operation = EOperation('op', params=(param1, param2))
    assert len(operation.eParameters) == 2
    assert operation.eParameters[0] is param1
    assert operation.eParameters[1] is param2
    assert operation.to_code()


def test_edatatype_instanceClass():
    Integer = EDataType('Integer', instanceClassName='java.lang.Integer')
    assert Integer.eType is int
    assert Integer.type_as_factory is False
    assert Integer.default_value is None
    assert Integer.instanceClassName == 'java.lang.Integer'
    assert Integer.to_string(45) == '45'

    Integer = EDataType('Integer', instanceClassName='int')
    assert Integer.eType is int
    assert Integer.type_as_factory is False
    assert Integer.default_value is 0
    assert Integer.instanceClassName == 'int'
    assert Integer.to_string(45) == '45'


def test_edatatype_instanceClass_unknown():
    Unknown = EDataType('Unknown', instanceClassName='unknown')
    assert Unknown.eType is object
    assert Unknown.type_as_factory is True
    assert Unknown.default_value is not None
    A = EClass('A')
    A.eStructuralFeatures.append(EAttribute('u', Unknown))
    a = A()
    assert a.u is not None
    assert isinstance(a.u, object)


def test_eattribute_dynamicaddition():
    A = EClass('A')
    a = A()
    names = EAttribute('names', EString, upper=-1)
    age = EAttribute('age', EInt)
    A.eStructuralFeatures.append(names)
    A.eStructuralFeatures.append(age)
    assert a.names == set()
    assert names.get_default_value() is None
    assert age.get_default_value() == 0
    assert a.age == 0


def test_eattribute_defaultvalue():
    A = EClass('A')
    A.eStructuralFeatures.append(EAttribute('name', EString, default_value='test'))
    a = A()
    assert a.name == 'test'

    a.name = 'new_test'
    assert a.name == 'new_test'


def test_eattribute_id():
    A = EClass('A')
    A.eStructuralFeatures.append(EAttribute('myid', EInt, iD=True))
    a = A()
    a.myid = 45
    assert a.myid == 45
    assert A.eStructuralFeatures[0].iD


def test_eattribute_edate():
    A = EClass('A')
    A.eStructuralFeatures.append(EAttribute('date', EDate))
    a = A()
    assert a.date is None

    a.date = datetime.now()
    assert a.date is not None

    with pytest.raises(BadValueError):
        a.date = 45


def test_eoperation_multiplicity():
    A = EClass('A')
    operation = EOperation('do_it', upper=-1)
    A.eOperations.append(operation)
    assert operation.many
    assert operation.upperBound == -1

    operation.lowerBound = 1
    assert operation.lowerBound == 1
    assert operation.upperBound == -1
    assert operation.many

    operation.upperBound = 1
    assert operation.lowerBound == 1
    assert operation.upperBound == 1
    assert operation.many is False

    a = A()
    with pytest.raises(NotImplementedError):
        a.do_it()


def test_eparameter_multiplicity():
    A = EClass('A')
    parameter = EParameter('param', required=False, lower=0, upper=-1)

    operation = EOperation('do_it', params=(parameter,))
    A.eOperations.append(operation)
    assert parameter.many
    assert parameter.upperBound == -1

    parameter.lowerBound = 1
    assert parameter.lowerBound == 1
    assert parameter.upperBound == -1
    assert parameter.many

    parameter.upperBound = 1
    assert parameter.lowerBound == 1
    assert parameter.upperBound == 1
    assert parameter.many is False

    a = A()
    with pytest.raises(NotImplementedError):
        a.do_it(param='test_value')


def test_eoperation_with_exception():
    E1 = EClass('E1')
    E2 = EClass('E2')
    operation = EOperation('operation', exceptions=(E1, E2))
    assert E1 in operation.eExceptions
    assert E2 in operation.eExceptions


def test_eattribute_notype():
    att = EAttribute('native')
    A = EClass('A')
    A.eStructuralFeatures.append(att)
    a = A()
    assert EcoreUtils.isinstance(a.native, ecore.ENativeType)
    assert isinstance(a.native, object)


def test_edatatype_isinstance():
    String = EDataType('String')
    assert EDataType.__isinstance__(String)
    assert EcoreUtils.isinstance(String, EDataType)


testdata = [
    (EAttribute('att'), EClassifier, False),
    (EOperation('op'), EClassifier, False),
    (EPackage('pack'), EClassifier, False),
    (EClass('e'), EClassifier, True),
    (EAttribute, EClassifier, True),
    (EClass, EClassifier, True),
    (EPackage, EClassifier, True),

    (EAttribute('att'), EPackage, False),
    (EOperation('op'), EPackage, False),
    (EPackage('pack'), EPackage, True),
    (EClass('e'), EPackage, False),
]


@pytest.mark.parametrize("instance, cls, result", testdata)
def test_epackage_isinstance(instance, cls, result):
    assert EcoreUtils.isinstance(instance, cls) is result


def test_eclass__name__():
    A = EClass('A')
    assert A.name == 'A'
    assert A.python_class.__name__ == 'A'
    assert A.__name__ == 'A'

    A.name = 'B'
    assert A.name == 'B'
    assert A.python_class.__name__ == 'B'
    assert A.__name__ == 'B'


def test_ecollection_iadd():
    A = EClass('A')
    A.eStructuralFeatures += EReference('a', A, upper=-1)

    assert len(A.eStructuralFeatures) == 1

    a = A()
    a.a += [A(), A()]
    assert len(a.a) == 2

    with pytest.raises(BadValueError):
        a.a += 'test'

    with pytest.raises(BadValueError):
        a.a += [A(), 'test']


def test_eobject_dir():
    A = EClass('A')
    assert 'name' in dir(A)  # just an example

    a = A()
    assert dir(a) == []

    A.eStructuralFeatures.append(EAttribute('name', EString))
    A.eStructuralFeatures.append(EReference('to_a', A))
    assert 'name' in dir(a)
    assert 'to_a' in dir(a)


def test_eobject_kargs_init():
    A = EClass('A')
    a = A(test='test_value')
    assert a.test == 'test_value'

    del a.test
    A.eStructuralFeatures.append(EAttribute('test', EString))
    a.test = 'new_value'
    assert a.test == 'new_value'

    with pytest.raises(BadValueError):
        a.test = 4


def test_eenum_defaultvalue_computed():
    E = EEnum('enum')
    A = EEnumLiteral(name='A')
    E.eLiterals.append(A)
    B = EEnumLiteral(name='B')
    E.eLiterals.append(B)
    C = EEnumLiteral(name='C')
    E.eLiterals.append(C)
    assert E.default_value is A

    E.default_value = 'B'
    assert E.default_value is B
    assert E.eLiterals[0] is B

    with pytest.raises(AttributeError):
        E.default_value = 'D'

    D = EEnumLiteral(name='D')
    E.eLiterals.insert(0, D)
    assert E.default_value is D

    assert E.from_string('A') is A
    assert E.to_string(A) is 'A'


def test_eclass_isinstance():
    A = EClass('A')
    B = EClass('B', superclass=(A,))

    b = B()
    assert isinstance(b, B)
    assert isinstance(b, A)

    MetaA = EClass('MetaA', superclass=(EClass.eClass,))
    A = MetaA('A')
    a = A()

    assert isinstance(a, A)
    assert isinstance(MetaA, EClass)


def test_edatatype_direct_isinstance():
    assert isinstance('string', EString)
    assert isinstance(3, EInt)

    MyDatatype = EDataType('MyDatatype', eType=complex)
    assert isinstance(3+4j, MyDatatype)


def test_eenum_isinstance():
    MyEnum = EEnum('MyEnum', literals=('A', 'B', 'C'))
    assert isinstance(MyEnum.A, MyEnum)


def test_eall_ref_attrs():
    A = EClass('A')
    A.eStructuralFeatures.append(EAttribute('name', EString))
    A.eStructuralFeatures.append(EReference('toa', A))

    B = EClass('B', superclass=(A,))

    assert B.eAllReferences() == {A.eStructuralFeatures[1]}
    assert B.eAllAttributes() == {A.eStructuralFeatures[0]}


def test_allContent_derived_containment():
    A = EClass('A')
    A.eStructuralFeatures.append(EReference('a', A, containment=True))
    A.eStructuralFeatures.append(EReference('b', A, derived=True,
                                            containment=True))

    a1, a2 = A(), A()
    a1.a = a2
    assert a2 in a1.eContents


def test_explicit_eobject_inheritance():
    A = EClass('A', superclass=(EObject.eClass))

    assert isinstance(A, EObject)


def test_containerswitching():
    A = EClass('A')
    A.eStructuralFeatures.append(EReference('toa', A, containment=True))

    a1 = A()
    a2 = A()
    assert a2.eContainer() is None
    assert a2.eContainmentFeature() is None

    a1.toa = a2
    assert a2.eContainer() is a1
    assert a2.eContainmentFeature() is A.eStructuralFeatures[0]

    a3 = A()
    a4 = A()
    a4.toa = a3
    assert a3.eContainer() is a4
    assert a3.eContainmentFeature() is A.eStructuralFeatures[0]

    a1.toa = a3
    assert a3.eContainer() is a1
    assert a2.eContainer() is None
    assert a2.eContainmentFeature() is None


def test_structuralfeature_many_computation():
    attrib = EAttribute('attrib')
    assert attrib.many is False

    attrib.upperBound = -1
    assert attrib.many is True

    attrib.lowerBound = 2
    assert attrib.many is True

    attrib.upperBound = attrib.lowerBound
    assert attrib.many is False
