import pytest
from pyecore.ecore import *


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
    assert a.names == []
    with pytest.raises(BadValueError):
        a.names = 'test'


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
    assert a1.tob and b1 in a1.tob and len(a1.tob) == 1


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
    assert EcoreUtils.getRoot(b1) is a1
    assert EcoreUtils.getRoot(None) is None
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
    # assert isinstance(a1.tob, ESet)
    assert isinstance(a1.tob, EOrderedSet)
    assert b1 in a1.tob


def test_create_dynamic_ereference_nonord_nonuni():
    A = EClass('A')
    B = EClass('B')
    A.eStructuralFeatures.append(EReference('tob', B, unique=False, upper=-1, ordered=False))
    a1 = A()
    b1 = B()
    a1.tob.append(b1)
    assert isinstance(a1.tob, EList)
    assert b1 in a1.tob


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
