
from .TransformationTrace import getEClassifier, eClassifiers
from .TransformationTrace import name, nsURI, nsPrefix, eClass
from .TransformationTrace import EGenericType
from .TransformationTrace import Artefact, Rule, Record, ObjectReference, Attribute, TransformationTrace

from pyecore.ecore import EObject, EStructuralFeature

from . import TransformationTrace

__all__ = ['Artefact', 'Rule', 'Record', 'ObjectReference', 'Attribute', 'TransformationTrace']

eSubpackages = []
eSuperPackage = None
TransformationTrace.eSubpackages = eSubpackages
TransformationTrace.eSuperPackage = eSuperPackage

Artefact.feature.eType = EStructuralFeature

Rule.records.eType = Record

Rule.transformation.eType = TransformationTrace

Record.inputs.eType = Artefact

Record.outputs.eType = Artefact

Record.rule.eType = Rule

ObjectReference.old_value.eType = EObject

ObjectReference.new_value.eType = EObject

TransformationTrace.rules.eType = Rule


otherClassifiers = []

for classif in otherClassifiers:
    eClassifiers[classif.name] = classif
    classif.ePackage = eClass

for classif in eClassifiers.values():
    eClass.eClassifiers.append(classif.eClass)

for subpack in eSubpackages:
    eClass.eSubpackages.append(subpack.eClass)
