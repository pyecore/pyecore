====================================================================
PyEcore: A Pythonic Implementation of the Eclipse Modeling Framework
====================================================================

|pypi-version| |master-build| |coverage| |code-quality| |license|

.. |master-build| image:: https://travis-ci.org/pyecore/pyecore.svg?branch=master
    :target: https://travis-ci.org/pyecore/pyecore

.. |develop-build| image:: https://travis-ci.org/pyecore/pyecore.svg?branch=develop
    :target: https://travis-ci.org/pyecore/pyecore

.. |pypi-version| image:: https://badge.fury.io/py/pyecore.svg
    :target: https://badge.fury.io/py/pyecore

.. |coverage| image:: https://coveralls.io/repos/github/pyecore/pyecore/badge.svg?branch=master
    :target: https://coveralls.io/github/pyecore/pyecore?branch=master

.. |license| image:: https://img.shields.io/badge/license-New%20BSD-blue.svg
    :target: https://raw.githubusercontent.com/pyecore/pyecore/master/LICENSE

.. |code-quality| image:: https://api.codacy.com/project/badge/Grade/ed038354821f43e7a4579c6a14185cdf
    :target: https://www.codacy.com/app/aranega/pyecore

PyEcore is a Model Driven Engineering (MDE) framework written for Python.
Precisely, it is an implementation of `EMF/Ecore
<https://www.eclipse.org/modeling/emf/>`_ for Python, and it tries to give an
API which is compatible with the original EMF Java implementation.

PyEcore allows you to handle models and metamodels (structured data model), and
gives the key you need for building MDE-based tools and other applications based
on a structured data model. It supports out-of-the-box:

* Data inheritance,
* Two-ways relationship management (opposite references),
* XMI (de)serialization,
* JSON (de)serialization,
* Notification system,
* Reflexive API...

Let see how to create on a very simple "dynamic" metamodel (in opposite to
static ones, see the `documentation <https://pyecore.readthedocs.io/en/latest/>`_
for more details):

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
a ``name``, and it exists a containment relationship between them. This relation
is bi-directionnal, which means that each time a ``Node`` object is added to the
``nodes`` relationship of a ``Graph``, the ``owned_by`` relation of the ``Node``
is updated also (it also work in the other way).

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


This example gives a quick overview of some of the features you get for free
when using PyEcore.

*The project slowly grows and it still requires more love.*

Installation
============

PyEcore is available on ``pypi``, you can simply install it using ``pip``:

.. code-block:: bash

    $ pip install pyecore

The installation can also be performed manually (better in a virtualenv):

.. code-block:: bash

    $ python setup.py install


Documentation
=============

You can read the documentation at this address:

https://pyecore.readthedocs.io/en/latest/


Dependencies
============

The dependencies required by pyecore are:

* ordered-set which is used for the ``ordered`` and ``unique`` collections expressed in the metamodel,
* lxml which is used for the XMI parsing.

These dependencies are directly installed if you choose to use ``pip``.


Run the Tests
=============

Tests uses `py.test` and 'coverage'. Everything is driven by `Tox`, so in order
to run the tests simply run:

.. code-block:: bash

    $ tox


Liberty Regarding the Java EMF Implementation
=============================================

* There is some meta-property that could be missing inside PyEcore. If you see one missing, please open a new ticket!
* Proxies are not "removed" once resolved as in the the Java version, instead they acts as transparent proxies and redirect each calls to the 'proxied' object.
* PyEcore is able to automatically load some model/metamodel dependencies on its own.

State
=====

In the current state, the project implements:

* the dynamic/static metamodel definitions,
* reflexive API,
* inheritance,
* enumerations,
* abstract metaclasses,
* runtime typechecking,
* attribute/reference creations,
* collections (attribute/references with upper bound set to ``-1``),
* reference eopposite,
* containment reference,
* introspection,
* select/reject on collections,
* Eclipse XMI import (partially, only single root models),
* Eclipse XMI export (partially, only single root models),
* simple notification/Event system,
* EOperations support,
* code generator for the static part,
* EMF proxies (first version),
* object deletion (first version),
* EMF commands (first version),
* EMF basic command stack,
* EMF very basic Editing Domain,
* JSON import (simple JSON format),
* JSON export (simple JSON format),
* introduce behavior @runtime,
* resources auto-load for some cross-references,
* derived collections,
* multiple roots ressources,
* ``xsi:schemaLocation`` support for XMI resources,
* URI mapper like,
* ``EGeneric`` support (first simple version),
* URI converter like

The things that are in the roadmap:

* new implementation of ``EOrderedSet``, ``EList``, ``ESet`` and ``EBag``,
* new implementation of ``EStringToStringMapEntry`` and ``EFeatureMapEntry``,
* improve documentation,
* copy/paste (?).

Existing Projects
=================

There is not so much projects proposing to handle model and metamodel in Python.
The only projects I found are:

* PyEMOF (http://www.lifl.fr/~marvie/software/pyemof.html)
* EMF4CPP (https://github.com/catedrasaes-umu/emf4cpp)
* PyEMOFUC (http://www.istr.unican.es/pyemofuc/index_En.html)

PyEMOF proposes an implementation of the OMG's EMOF in Python. The project
targets Python2, only supports Class/Primitive Types (no Enumeration), XMI
import/export and does not provide a reflexion layer. The project didn't move
since 2005.

EMF4CPP proposes a C++ implementation of EMF. This implementation also
introduces Python scripts to call the generated C++ code from a Python
environment. It seems that the EMF4CPP does not provide a reflexive layer
either.

PyEMOFUC proposes, like PyEMOF, a pure Python implementation of the OMG's EMOF.
If we stick to a kind of EMF terminology, PyEMOFUC only supports dynamic
metamodels and seems to provide a reflexive layer. The project does not appear
seems to have moved since a while.

Contributors
============

Thanks for making PyEcore better!

* Mike Pagel (`@moltob <https://github.com/moltob>`_), which is also the author
  of `pyecoregen <https://github.com/pyecore/pyecoregen>`_ and `pymultigen <https://github.com/moltob/pymultigen>`_ (on which pyecoregen is based)
* Terry Kingston (`@TerryKingston <https://github.com/TerryKingston>`_)
* Afonso Pinto (`@afonsobspinto <https://github.com/afonsobspinto>`_)
* Andy (`@CFAndy <https://github.com/CFAndy>`_)
* annighoefer (`@annighoefer <https://github.com/annighoefer>`_)
* Rodriguez Facundo (`@rodriguez-facundo <https://github.com/rodriguez-facundo>`_)
* Filippo Ledda (`@filippometacell <https://github.com/filippometacell>`_)
* Ewoud Werkman (`@ewoudwerkman <https://github.com/ewoudwerkman>`_)



Additional Resources
====================

* `This article <http://modeling-languages.com/pyecore-python-eclipse-modeling-framework>`_
  on the blog of the Professor Jordi Cabot gives more information and
  implementations details about PyEcore.
