import typing
import functools
import pyecore.ecore as Ecore
from pyecore.resources import ResourceSet, Resource, URI
from m2mlib import mapping, mappingwhen, disjunct


def _for_(col, body=lambda x: x, separator=''):
    result = []
    for c in col:
        result.append(str(body(c)))
    return separator.join(result)

# CACHE
map_result = {}


# @mappingwhen(lambda self, x: isinstance(self, A) and x > 0)
# def A_map1(self : A, x : int) -> A:
#     _result_.name = self.name + '_a'
#     print(_result_.name)
#
#
# @when(lambda self, x: isinstance(self, B) and x > 0)
# @mapping
# def B_map1(self : B, x : int) -> B:
#     _result_.name = self.name + '_b'
#     print(_result_.name)
#
#
# @disjunct(A_map1, B_map1)
# def map1(self : object, x : int) -> typing.Any:
#     pass


@mapping
def createEPackage(self: Ecore.EPackage) -> Ecore.EPackage:
    result.name = self.name + 'Copy'
    result.nsURI = self.nsURI
    result.nsPrefix = self.nsPrefix
    for x in self.eClassifiers:
        result.eClassifiers.append(createEClass(x, result))


@when(lambda self, parent: self.name)
@mapping
def createEClass(self: Ecore.EClass, parent: Ecore.EPackage) -> Ecore.EClass:
    result.name = self.name + 'Copy'
    result.abstract = self.abstract
    for attribute in self.eAttributes:
        result.eStructuralFeatures.append(copyEAttribute(attribute))
    parent.eClassifiers.append(self)


@mapping
def copyEAttribute(self: Ecore.EAttribute) -> Ecore.EAttribute:
    result.name = self.name + 'Copy'
    result.lowerBound = self.lowerBound
    result.upperBound = self.upperBound
    result.eType = self.eType


root = Ecore.EPackage('test')
A1 = Ecore.EClass('A1')
root.eClassifiers.append(A1)
A1.eStructuralFeatures.append(Ecore.EAttribute('name', eType=Ecore.EString))

inPackage = root
result = createEPackage(inPackage)

rset = ResourceSet()
outresource = rset.create_resource(URI('testt.xmi'))
outresource.append(result)
outresource.save()
