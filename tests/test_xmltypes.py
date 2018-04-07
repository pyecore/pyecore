import pytest
from pyecore.resources import global_registry
import pyecore.type as XMLTypes
from pyecore.ecore import BadValueError, EOrderedSet


def test__registration():
    assert XMLTypes.nsURI in global_registry


def test__xmltypes_ePackage():
    epackage = XMLTypes.eClass
    assert XMLTypes.String.ePackage is epackage
    assert XMLTypes.AnyType.eClass.ePackage is epackage


def test__simple_any_type_bad_arg():
    with pytest.raises(AttributeError):
        XMLTypes.SimpleAnyType(not_arg='test')


def test__simple_any_type():
    simple = XMLTypes.SimpleAnyType()
    assert simple.rawValue is None
    assert simple.value is None
    assert simple.instanceType is None
    assert simple.mixed == {}
    assert simple.any == {}
    assert simple.anyAttribute == {}

    simple.any = {'test': 0}
    assert simple.any['test'] == 0

    with pytest.raises(BadValueError):
        simple.any = 4


def test__simple_any_type_full():
    simple = XMLTypes.SimpleAnyType(any={'test': 0}, mixed={'mix_test': 'val'},
                                    anyAttribute={'any_att': 'anyVal'},
                                    rawValue='0', value=0,
                                    instanceType=XMLTypes.Integer)
    assert simple.any['test'] == 0
    assert simple.anyAttribute['any_att'] == 'anyVal'
    assert simple.mixed['mix_test'] == 'val'


def test__ProcessingInstruction_full():
    instruction = XMLTypes.ProcessingInstruction(data='my_data',
                                                 target='my_target')
    assert instruction.data == 'my_data'
    assert instruction.target == 'my_target'


def test__ProcessingInstruction_bad_args():
    with pytest.raises(AttributeError):
        XMLTypes.ProcessingInstruction(my_data='test')


def test__XMLTypeDocumentRoot_full():
    inst = XMLTypes.ProcessingInstruction()
    document = XMLTypes.XMLTypeDocumentRoot(mixed={'x': 0},
                                            xMLNSPrefixMap={'y': 1},
                                            xSISchemaLocation={'z': 2},
                                            processingInstruction=(inst,))
    assert document.mixed['x'] == 0
    assert document.xMLNSPrefixMap['y'] == 1
    assert document.xSISchemaLocation['z'] == 2
    assert inst in document.processingInstruction

    document.cDATA = EOrderedSet(document, XMLTypes.XMLTypeDocumentRoot._cDATA)
    document.cDATA.append('v1')
    assert 'v1' in document.cDATA

    document.text = EOrderedSet(document, XMLTypes.XMLTypeDocumentRoot._text)
    document.text.append('v2')
    assert 'v2' in document.text

    document.comment = EOrderedSet(document, XMLTypes.XMLTypeDocumentRoot
                                   ._comment)
    document.comment.append('v3')
    assert 'v3' in document.comment


def test__XMLTypeDocumentRoot_bad_args():
    with pytest.raises(AttributeError):
        XMLTypes.XMLTypeDocumentRoot(my_arg='test')

    with pytest.raises(AttributeError):
        XMLTypes.XMLTypeDocumentRoot(cDATA=('my_data',))

    with pytest.raises(AttributeError):
        XMLTypes.XMLTypeDocumentRoot(comment=('my_comment',))

    with pytest.raises(AttributeError):
        XMLTypes.XMLTypeDocumentRoot(text=('my_text',))
