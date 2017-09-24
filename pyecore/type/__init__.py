"""
Implementation of EMF XMLTypes. This implementation is not automatically
registered in the 'global_registry' if directly imported. The automatic
registration is performed when 'resources' is used.

This implementation had been almost fully generated using pyecoregen. The only
manual intervention required are:
 - addition of the missing import for 'EDataType' and 'EStringToStringMapEntry'
   in '__init__.py'
 - addition of 'from_string' and 'to_string' lambdas for required types

Still missing are a proper translation for Java types:
 - 'javax.xml.datatype.XMLGregorianCalendar'
 - 'javax.xml.datatype.Duration'
 - 'javax.xml.namespace.QName'
"""

from ..ecore import EDataType, EStringToStringMapEntry
from ..resources import global_registry, Resource
from .type import getEClassifier, eClassifiers  # noqa
from .type import name, nsURI, nsPrefix, eClass  # noqa
from .type import AnySimpleType, AnyType, AnyURI, Base64Binary, Boolean, \
                  BooleanObject, Byte, ByteObject, Date, DateTime, Decimal, \
                  Double, DoubleObject, Duration, ENTITIES, ENTITIESBase, \
                  ENTITY, Float, FloatObject, GDay, GMonth, GMonthDay, GYear, \
                  GYearMonth, HexBinary, ID, IDREF, IDREFS, IDREFSBase, Int, \
                  Integer, IntObject, Language, Long, LongObject, Name, \
                  NCName, NegativeInteger, NMTOKEN, NMTOKENS, NMTOKENSBase, \
                  NonNegativeInteger, NonPositiveInteger, NormalizedString, \
                  NOTATION, PositiveInteger, ProcessingInstruction, QName, \
                  Short, ShortObject, SimpleAnyType, String, Time, Token, \
                  UnsignedByte, UnsignedByteObject, UnsignedInt, \
                  UnsignedIntObject, UnsignedLong, UnsignedShort, \
                  UnsignedShortObject, XMLTypeDocumentRoot
# from . import type

__all__ = ['AnySimpleType', 'AnyType', 'AnyURI', 'Base64Binary', 'Boolean',
           'BooleanObject', 'Byte', 'ByteObject', 'Date', 'DateTime',
           'Decimal', 'Double', 'DoubleObject', 'Duration', 'ENTITIES',
           'ENTITIESBase', 'ENTITY', 'Float', 'FloatObject', 'GDay', 'GMonth',
           'GMonthDay', 'GYear', 'GYearMonth', 'HexBinary', 'ID', 'IDREF',
           'IDREFS', 'IDREFSBase', 'Int', 'Integer', 'IntObject', 'Language',
           'Long', 'LongObject', 'Name', 'NCName', 'NegativeInteger',
           'NMTOKEN', 'NMTOKENS', 'NMTOKENSBase', 'NonNegativeInteger',
           'NonPositiveInteger', 'NormalizedString', 'NOTATION',
           'PositiveInteger', 'ProcessingInstruction', 'QName', 'Short',
           'ShortObject', 'SimpleAnyType', 'String', 'Time', 'Token',
           'UnsignedByte', 'UnsignedByteObject', 'UnsignedInt',
           'UnsignedIntObject', 'UnsignedLong', 'UnsignedShort',
           'UnsignedShortObject', 'XMLTypeDocumentRoot']

eSubpackages = []
eSuperPackage = None

SimpleAnyType.instanceType.eType = EDataType
XMLTypeDocumentRoot.xMLNSPrefixMap.eType = EStringToStringMapEntry
XMLTypeDocumentRoot.xSISchemaLocation.eType = EStringToStringMapEntry
XMLTypeDocumentRoot.processingInstruction.eType = ProcessingInstruction

otherClassifiers = [AnySimpleType, AnyURI, Base64Binary, Boolean,
                    BooleanObject, Byte, ByteObject, Date, DateTime, Decimal,
                    Double, DoubleObject, Duration, ENTITIES, ENTITIESBase,
                    ENTITY, Float, FloatObject, GDay, GMonth, GMonthDay, GYear,
                    GYearMonth, HexBinary, ID, IDREF, IDREFS, IDREFSBase, Int,
                    Integer, IntObject, Language, Long, LongObject, Name,
                    NCName, NegativeInteger, NMTOKEN, NMTOKENS, NMTOKENSBase,
                    NonNegativeInteger, NonPositiveInteger, NormalizedString,
                    NOTATION, PositiveInteger, QName, Short, ShortObject,
                    String, Time, Token, UnsignedByte, UnsignedByteObject,
                    UnsignedInt, UnsignedIntObject, UnsignedLong,
                    UnsignedShort, UnsignedShortObject]

for classif in otherClassifiers:
    eClassifiers[classif.name] = classif
    classif.ePackage = eClass

for classif in eClassifiers.values():
    eClass.eClassifiers.append(classif.eClass)

# We comment this as there is no subpackages for XMLTypes
# for subpack in eSubpackages:
#    eClass.eSubpackages.append(subpack.eClass)

global_registry[eClass.nsURI] = eClass
xmltypes_resource = Resource(uri=eClass.nsURI)
xmltypes_resource.append(eClass)
