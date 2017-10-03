"""Definition of meta model 'type' for XMLTypes."""
from functools import partial
import pyecore.ecore as Ecore
from pyecore.ecore import EPackage, EDataType, EObject, MetaEClass, \
                          EAttribute, EFeatureMapEntry, EReference


name = 'type'
nsURI = 'http://www.eclipse.org/emf/2003/XMLType'
nsPrefix = 'ecore.xml.type'

eClass = EPackage(name=name, nsURI=nsURI, nsPrefix=nsPrefix)

eClassifiers = {}
getEClassifier = partial(Ecore.getEClassifier, searchspace=eClassifiers)

AnySimpleType = EDataType('AnySimpleType',
                          instanceClassName='java.lang.Object')

AnyURI = EDataType('AnyURI', instanceClassName='java.lang.String')

Base64Binary = EDataType('Base64Binary', instanceClassName='byte[]')

Boolean = EDataType('Boolean', instanceClassName='boolean',
                    to_string=lambda x: str(x).lower(),
                    from_string=lambda x: x in ['True', 'true'])

BooleanObject = EDataType('BooleanObject',
                          instanceClassName='java.lang.Boolean',
                          to_string=lambda x: str(x).lower(),
                          from_string=lambda x: x in ['True', 'true'])

Byte = EDataType('Byte', instanceClassName='byte')

ByteObject = EDataType('ByteObject', instanceClassName='java.lang.Byte')

Date = EDataType('Date',
                 instanceClassName='javax.xml.datatype.XMLGregorianCalendar')

DateTime = EDataType('DateTime',
                     instanceClassName='javax.xml.datatype.'
                                       'XMLGregorianCalendar')

Decimal = EDataType('Decimal', instanceClassName='java.math.BigDecimal',
                    from_string=lambda x: int(x))

Double = EDataType('Double', instanceClassName='double',
                   from_string=lambda x: float(x))

DoubleObject = EDataType('DoubleObject', instanceClassName='java.lang.Double',
                         from_string=lambda x: float(x))

Duration = EDataType('Duration',
                     instanceClassName='javax.xml.datatype.Duration')

ENTITIES = EDataType('ENTITIES', instanceClassName='java.util.List')

ENTITIESBase = EDataType('ENTITIESBase', instanceClassName='java.util.List')

ENTITY = EDataType('ENTITY', instanceClassName='java.lang.String')

Float = EDataType('Float', instanceClassName='float',
                  from_string=lambda x: float(x))

FloatObject = EDataType('FloatObject', instanceClassName='java.lang.Float',
                        from_string=lambda x: float(x))

GDay = EDataType('GDay',
                 instanceClassName='javax.xml.datatype.XMLGregorianCalendar')

GMonth = EDataType('GMonth',
                   instanceClassName='javax.xml.datatype.XMLGregorianCalendar')

GMonthDay = EDataType('GMonthDay',
                      instanceClassName='javax.xml.datatype.'
                                        'XMLGregorianCalendar')

GYear = EDataType('GYear',
                  instanceClassName='javax.xml.datatype.XMLGregorianCalendar')

GYearMonth = EDataType('GYearMonth',
                       instanceClassName='javax.xml.datatype.'
                                         'XMLGregorianCalendar')

HexBinary = EDataType('HexBinary', instanceClassName='byte[]')

ID = EDataType('ID', instanceClassName='java.lang.String')

IDREF = EDataType('IDREF', instanceClassName='java.lang.String')

IDREFS = EDataType('IDREFS', instanceClassName='java.util.List')

IDREFSBase = EDataType('IDREFSBase', instanceClassName='java.util.List')

Int = EDataType('Int', instanceClassName='int')

Integer = EDataType('Integer', instanceClassName='java.math.BigInteger',
                    from_string=lambda x: int(x))

IntObject = EDataType('IntObject', instanceClassName='java.lang.Integer',
                      from_string=lambda x: int(x))

Language = EDataType('Language', instanceClassName='java.lang.String')

Long = EDataType('Long', instanceClassName='long',
                 from_string=lambda x: int(x))

LongObject = EDataType('LongObject', instanceClassName='java.lang.Long',
                       from_string=lambda x: int(x))

Name = EDataType('Name', instanceClassName='java.lang.String')

NCName = EDataType('NCName', instanceClassName='java.lang.String')

NegativeInteger = EDataType('NegativeInteger',
                            instanceClassName='java.math.BigInteger',
                            from_string=lambda x: int(x))

NMTOKEN = EDataType('NMTOKEN', instanceClassName='java.lang.String')

NMTOKENS = EDataType('NMTOKENS', instanceClassName='java.util.List')

NMTOKENSBase = EDataType('NMTOKENSBase', instanceClassName='java.util.List')

NonNegativeInteger = EDataType('NonNegativeInteger',
                               instanceClassName='java.math.BigInteger',
                               from_string=lambda x: int(x))

NonPositiveInteger = EDataType('NonPositiveInteger',
                               instanceClassName='java.math.BigInteger',
                               from_string=lambda x: int(x))

NormalizedString = EDataType('NormalizedString',
                             instanceClassName='java.lang.String')

NOTATION = EDataType('NOTATION', instanceClassName='javax.xml.namespace.QName')

PositiveInteger = EDataType('PositiveInteger',
                            instanceClassName='java.math.BigInteger',
                            from_string=lambda x: int(x))

QName = EDataType('QName', instanceClassName='javax.xml.namespace.QName')

Short = EDataType('Short', instanceClassName='short',
                  from_string=lambda x: int(x))

ShortObject = EDataType('ShortObject', instanceClassName='java.lang.Short',
                        from_string=lambda x: int(x))

String = EDataType('String', instanceClassName='java.lang.String')

Time = EDataType('Time',
                 instanceClassName='javax.xml.datatype.XMLGregorianCalendar')

Token = EDataType('Token', instanceClassName='java.lang.String')

UnsignedByte = EDataType('UnsignedByte', instanceClassName='short',
                         from_string=lambda x: int(x))

UnsignedByteObject = EDataType('UnsignedByteObject',
                               instanceClassName='java.lang.Short',
                               from_string=lambda x: int(x))

UnsignedInt = EDataType('UnsignedInt', instanceClassName='long',
                        from_string=lambda x: int(x))

UnsignedIntObject = EDataType('UnsignedIntObject',
                              instanceClassName='java.lang.Long',
                              from_string=lambda x: int(x))

UnsignedLong = EDataType('UnsignedLong',
                         instanceClassName='java.math.BigInteger',
                         from_string=lambda x: int(x))

UnsignedShort = EDataType('UnsignedShort', instanceClassName='int',
                          from_string=lambda x: int(x))

UnsignedShortObject = EDataType('UnsignedShortObject',
                                instanceClassName='java.lang.Integer',
                                from_string=lambda x: int(x))


# mixed, any and anyAttribute should have upper=-1 (but dict this implies)
# modifications on the EFeatureMapEntry data type which currently considered
# as dict.
# As consequence, in the constructor, 'extend' is not called anymore, but
# 'update' is called instead.
class AnyType(EObject, metaclass=MetaEClass):

    mixed = EAttribute(eType=EFeatureMapEntry, derived=False, changeable=True,
                       iD=False, upper=1)
    _any = EAttribute(eType=EFeatureMapEntry, derived=True,
                      changeable=True, iD=False, upper=1, name='any')
    anyAttribute = EAttribute(eType=EFeatureMapEntry, derived=False,
                              changeable=True, iD=False, upper=1)

    @property
    def any(self):
        return self._any

    @any.setter
    def any(self, value):
        self._any = value

    def __init__(self, *, mixed=None, any=None, anyAttribute=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if mixed:
            self.mixed.update(mixed)

        if any:
            self.any.update(any)

        if anyAttribute:
            self.anyAttribute.update(anyAttribute)


class ProcessingInstruction(EObject, metaclass=MetaEClass):

    data = EAttribute(eType=String, derived=False, changeable=True, iD=False)
    target = EAttribute(eType=String, derived=False, changeable=True, iD=False)

    def __init__(self, *, data=None, target=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if data is not None:
            self.data = data

        if target is not None:
            self.target = target


# mixed, xMLNSPrefixMap, xSISchemaLocation should have upper=-1 (but dict this
# implies) modifications on the EFeatureMapEntry data type which currently
# considered as dict.
# As consequence, in the constructor, 'extend' is not called anymore, but
# 'update' is called instead.
# Also, xMLNSPrefixMap and xSISchemaLocation have been tranformed as EAttribute
class XMLTypeDocumentRoot(EObject, metaclass=MetaEClass):

    mixed = EAttribute(eType=EFeatureMapEntry, derived=False, changeable=True,
                       iD=False, upper=1)
    _cDATA = EAttribute(eType=String, derived=True, changeable=True,
                        iD=False, upper=-1, name='cDATA')
    _comment = EAttribute(eType=String, derived=True, changeable=True,
                          iD=False, upper=-1, name='comment')
    _text = EAttribute(eType=String, derived=True, changeable=True, iD=False,
                       upper=-1, name='text')
    xMLNSPrefixMap = EAttribute(ordered=True, unique=True, upper=1)
    xSISchemaLocation = EAttribute(ordered=True, unique=True, upper=1)
    processingInstruction = EReference(ordered=True, unique=True,
                                       containment=True, upper=-1)

    @property
    def cDATA(self):
        return self._cDATA

    @cDATA.setter
    def cDATA(self, value):
        self._cDATA = value

    @property
    def comment(self):
        return self._comment

    @comment.setter
    def comment(self, value):
        self._comment = value

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value

    def __init__(self, *, mixed=None, xMLNSPrefixMap=None,
                 xSISchemaLocation=None, cDATA=None, comment=None,
                 processingInstruction=None, text=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if mixed:
            self.mixed.update(mixed)

        if cDATA:
            self.cDATA.extend(cDATA)

        if comment:
            self.comment.extend(comment)

        if text:
            self.text.extend(text)

        if xMLNSPrefixMap:
            self.xMLNSPrefixMap.update(xMLNSPrefixMap)

        if xSISchemaLocation:
            self.xSISchemaLocation.update(xSISchemaLocation)

        if processingInstruction:
            self.processingInstruction.extend(processingInstruction)


class SimpleAnyType(AnyType):

    _rawValue = EAttribute(eType=String, derived=True, changeable=True,
                           iD=False, name='rawValue')
    _value = EAttribute(eType=AnySimpleType, derived=True, changeable=True,
                        iD=False, name='value')
    instanceType = EReference(ordered=True, unique=True, containment=False)

    @property
    def rawValue(self):
        return self._rawValue

    @rawValue.setter
    def rawValue(self, value):
        self._rawValue = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value

    def __init__(self, *, rawValue=None, value=None, instanceType=None,
                 **kwargs):

        super().__init__(**kwargs)

        if rawValue is not None:
            self.rawValue = rawValue

        if value is not None:
            self.value = value

        if instanceType is not None:
            self.instanceType = instanceType
