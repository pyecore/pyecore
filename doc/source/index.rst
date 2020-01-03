.. PyEcore documentation master file, created by
   sphinx-quickstart on Tue Nov  7 09:26:41 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

PyEcore Documentation
=====================

|pypi-version| |master-build| |coverage| |license|

.. |master-build| image:: https://travis-ci.org/pyecore/pyecore.svg?branch=master
    :target: https://travis-ci.org/pyecore/pyecore

.. |pypi-version| image:: https://badge.fury.io/py/pyecore.svg
    :target: https://badge.fury.io/py/pyecore

.. |coverage| image:: https://coveralls.io/repos/github/pyecore/pyecore/badge.svg?branch=master
    :target: https://coveralls.io/github/pyecore/pyecore?branch=master

.. |license| image:: https://img.shields.io/badge/license-New%20BSD-blue.svg
    :target: https://raw.githubusercontent.com/pyecore/pyecore/master/LICENSE

PyEcore is a Model Driven Engineering (MDE) framework written for Python.
It is an implementation of `EMF/Ecore
<https://www.eclipse.org/modeling/emf/>`_ for Python, and tries to give an
API compatible with the original EMF Java implementation.

PyEcore allows you to create, load, modify, save and interact with models and metamodels,
to provide a framework to build MDE-based tools and other applications based
on a structured data model. It supports:

* Data inheritance
* Two-way relationship management (opposite references)
* XMI serialization and deserialization
* JSON serialization and deserialization
* Notification system
* Reflexive API

This example shows creation of simple "dynamic" metamodel (in contrast to
a static metamodel, as shown in "User Documentation"):

.. code-block:: python

    >>> from pyecore.ecore import EClass, EAttribute, EString, EObject
    >>> Graph = EClass('Graph')  # We create a 'Graph' concept
    >>> Node = EClass('Node')  # We create a 'Node' concept
    >>>
    >>> # We add a "name" attribute to the Graph concept
    >>> Graph.eStructuralFeatures.append(EAttribute('name', EString,
                                                    default_value='new_name'))
    >>> # And one on the 'Node' concept
    >>> Node.eStructuralFeatures.append(EAttribute('name', EString))
    >>>
    >>> # We now introduce a containment relation between Graph and Node
    >>> contains_nodes = EReference('nodes', Node, upper=-1, containment=True)
    >>> Graph.eStructuralFeatures.append(contains_nodes)
    >>> # We add an opposite relation between Graph and Node
    >>> Node.eStructuralFeatures.append(EReference('owned_by', Graph, eOpposite=contains_nodes))

With this code, we have defined two concepts: ``Graph`` and ``Node``. Both have
a ``name``, and there exists a containment relationship between them. This relation
is bi-directionnal, which means that each time a ``Node`` object is added to the
``nodes`` relationship of a ``Graph``, the ``owned_by`` relation of the ``Node``
is also updated also.  The reverse is also true, if a Graph were added to Node.owned_by.

Let's create some instances of our freshly created metamodel:

.. code-block:: python

    >>> # We create a Graph
    >>> g1 = Graph(name='Graph 1')
    >>> g1
    <pyecore.ecore.Graph at 0x7f0055554dd8>
    >>>
    >>> # And two node instances
    >>> n1 = Node(name='Node 1')
    >>> n2 = Node(name='Node 2')
    >>> n1, n2
    (<pyecore.ecore.Node at 0x7f0055550588>,
     <pyecore.ecore.Node at 0x7f00555502b0>)
    >>>
    >>> # We add them to the Graph
    >>> g1.nodes.extend([n1, n2])
    >>> g1.nodes
    EOrderedSet([<pyecore.ecore.Node object at 0x7f0055550588>,
                 <pyecore.ecore.Node object at 0x7f00555502b0>])
    >>>
    >>> # bi-directional references are updated
    >>> n1.owned_by
    <pyecore.ecore.Graph at 0x7f0055554dd8>


This example gives a quick overview of some of the features you get
when using PyEcore.


User Documentation
==================


.. toctree::
   :maxdepth: 2

   user/install
   user/quickstart
   user/advanced
   user/gmf_notation
   example/fsm_executable

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
