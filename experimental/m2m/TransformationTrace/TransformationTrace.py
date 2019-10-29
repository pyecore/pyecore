"""Definition of meta model 'TransformationTrace'."""
from functools import partial
import pyecore.ecore as Ecore
from pyecore.ecore import *


name = 'TransformationTrace'
nsURI = 'http://transformation_trace/1.0'
nsPrefix = 'TransformationTrace'

eClass = EPackage(name=name, nsURI=nsURI, nsPrefix=nsPrefix)

eClassifiers = {}
getEClassifier = partial(Ecore.getEClassifier, searchspace=eClassifiers)


@abstract
class Artefact(EObject, metaclass=MetaEClass):

    feature = EReference(ordered=True, unique=True, containment=False, derived=False)

    def __init__(self, *, feature=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if feature is not None:
            self.feature = feature


class Rule(EObject, metaclass=MetaEClass):

    name = EAttribute(eType=EString)
    records = EReference(ordered=True, unique=True, containment=True, derived=False, upper=-1)
    transformation = EReference(ordered=True, unique=True, containment=False, derived=False)

    def __init__(self, *, name=None, records=None, transformation=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if name is not None:
            self.name = name

        if records:
            self.records.extend(records)

        if transformation is not None:
            self.transformation = transformation


class Record(EObject, metaclass=MetaEClass):

    inputs = EReference(ordered=True, unique=True, containment=True, derived=False, upper=-1)
    outputs = EReference(ordered=True, unique=True, containment=True, derived=False, upper=-1)
    rule = EReference(ordered=True, unique=True, containment=False, derived=False)

    def __init__(self, *, inputs=None, outputs=None, rule=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if inputs:
            self.inputs.extend(inputs)

        if outputs:
            self.outputs.extend(outputs)

        if rule is not None:
            self.rule = rule


class TransformationTrace(EObject, metaclass=MetaEClass):

    rules = EReference(ordered=True, unique=True, containment=False, derived=False, upper=-1)

    def __init__(self, *, rules=None, **kwargs):
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if rules:
            self.rules.extend(rules)

    def __getitem__(self, rulename):
        rule = next((x for x in self.rules if x.name == rulename), None)
        if rule:
            return rule
        rule = Rule(name=rulename)
        self.rules.append(rule)
        return rule


class ObjectReference(Artefact):

    old_value = EReference(ordered=True, unique=True, containment=False, derived=False)
    new_value = EReference(ordered=True, unique=True, containment=False, derived=False)

    def __init__(self, *, old_value=None, new_value=None, **kwargs):

        super().__init__(**kwargs)

        if old_value is not None:
            self.old_value = old_value

        if new_value is not None:
            self.new_value = new_value


class Attribute(Artefact):

    old_value = EAttribute(eType=ENativeType, derived=False, changeable=True)
    new_value = EAttribute(eType=ENativeType, derived=False, changeable=True)

    def __init__(self, *, old_value=None, new_value=None, **kwargs):

        super().__init__(**kwargs)

        if old_value is not None:
            self.old_value = old_value

        if new_value is not None:
            self.new_value = new_value
