import motra

# generated using
# https://github.com/kolovos/datasets/blob/master/github-mde/ghmde.ecore
# as input metamodel
import ghmde
from pyecore.ecore import *

# Define a graph like metamodel in a static way
eClass = EPackage('graph', nsURI='http://graph/1.0', nsPrefix='graph')


@EMetaclass
class Node(object):
    name = EAttribute(eType=EString)


@EMetaclass
class Graph(object):
    name = EAttribute(eType=EString)
    nodes = EReference(eType=Node, upper=-1, containment=True)


# Transfo definition
ghmde2graph = motra.Transformation('ghmde2graph',
                                   inputs=['ghmde_model'],
                                   outputs=['graph_model'])


@ghmde2graph.main
def main(ghmde_model=None, graph_model=None):
    print('Transforming repository to graph', graph_model)
    for repository in motra.objects_of_kind(ghmde_model, ghmde.File):
        file2node(repository)
    for repository in motra.objects_of_kind(ghmde_model, ghmde.Repository):
        repository2graph(repository, postfix='_graph')


def does_not_starts_with(self, postfix):
    return not self.name.startswith(postfix)


@ghmde2graph.mapping(when=does_not_starts_with)
def repository2graph(self: ghmde.Repository, postfix: str) -> Graph:
    result.name = self.name + postfix
    for repo_file in self.files:
        result.nodes.append(file2node(repo_file))


@ghmde2graph.mapping
def file2node(self: ghmde.File) -> Node:
    result.name = self.path


# @transfo.main
# def main(inputs, outputs):
#     print('in main')
#     print(inputs.ghmde.contents)
#     for o in motra.objects_of_kind(inputs.ghmde, ghmde.Repository):
#         test_dispatch(o)
#
#
# @transfo.mapping(when=lambda self: self.name is not None)
# def test1(self: ghmde.Repository) -> ghmde.Repository:
#     print('changing name', result is self, self.name)
#     result.name = self.name
#     self.name += '_toto'
#
#
# @transfo.mapping(output_model='test2',
#                  when=lambda self: self.name is None)
# def test2(self: ghmde.Repository) -> ghmde.Repository:
#     result.name = 'from_empty_' + str(self)
#
#
# @transfo.disjunct(mappings=[test1, test2])
# def test_dispatch(self: ghmde.Repository) -> ghmde.Repository:
#     pass
