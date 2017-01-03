====================================================================
PyEcore: A Pythonic Implementation of the Eclipse Modeling Framework
====================================================================

.. highlight:: python

|master-build| (develop |develop-build|)

.. |master-build| image:: https://travis-ci.org/aranega/pyecore.svg?branch=master
    :target: https://travis-ci.org/aranega/pyecore

.. |develop-build| image:: https://travis-ci.org/aranega/pyecore.svg?branch=develop
    :target: https://travis-ci.org/aranega/pyecore

PyEcore is a "Pythonic?" (sounds pretentious) implementation of EMF/Ecore for
Python3. It's purpose is to handle model/metamodels in Python almost the same
way the Java version does.

However, PyEcore enables you to use a simple ``instance.attribute`` notation
instead of ``instance.setAttribute(...)/getAttribute(...)`` for the Java
version. To achieve this, PyEcore relies on reflection (a lot).

Let see by yourself how it works on a very simple metamodel created on
the fly (dynamic metamodel):

.. code-block:: python

    >>> from pyecore.ecore import EClass, EAttribute, EString, EObject
    >>> A = EClass('A') # We create metaclass named 'A'
    >>> A.eStructuralFeatures.append(EAttribute('myname', EString, default_value='new_name')) # We add a name attribute to the A metaclass
    >>> a1 = A()
    >>> a1.myname
    'new_name'
    >>> a1.myname = 'a_instance'
    >>> a1.myname
    'a_instance'
    >>> isinstance(a1, EObject)
    True

PyEcore also support introspection and the EMF reflexive API using basic Python
reflexive features:

.. code-block:: python

    >>> a1.eClass # some introspection
    <EClass name="A">
    >>> a1.eClass.eClass
    <EClass name="EClass">
    >>> a1.eClass.eClass is a1.eClass.eClass.eClass
    True
    >>> a1.eClass.eStructuralFeatures
    (<pyecore.ecore.EAttribute at 0x7f6bf6cd91d0>,)
    >>> a1.eClass.eStructuralFeatures[0].name
    'myname'
    >>> a1.eClass.eStructuralFeatures[0].eClass
    <EClass name="EAttribute">
    >>> a1.__getattribute__('name')
    'a_instance'
    >>> a1.__setattr__('myname', 'reflexive')
    >>> a1.__getattribute__('myname')
    'reflexive'

Runtime type checking is also performed (regarding what you expressed in your)
metamodel:

.. code-block:: python

    >>> a1.myname = 1
    Traceback (most recent call last):
        File "<stdin>", line 1, in <module>
        File ".../pyecore/ecore.py", line 66, in setattr
            raise BadValueError(got=value, expected=estruct.eType)
    pyecore.ecore.BadValueError: Expected type EString(str), but got type int with value 1 instead


PyEcore does support dynamic metamodel and static ones (see details in next
sections).

*The project is at an early stage and still requires more love.*

Dynamic Metamodels
==================

Dynamic metamodels reflects the ability to create metamodels "on-the-fly". You
can create metaclass hierarchie, add ``EAttribute`` and ``EReference``.

In order to create a new metaclass, you need to create an ``EClass`` instance:

.. code-block:: python

    >>> import pyecore.ecore as Ecore
    >>> MyMetaclass = Ecore.EClass('MyMetaclass')

You can then create instances of your metaclass:

.. code-block:: python

    >>> instance1 = MyMetaclass()
    >>> instance2 = MyMetaclass()
    >>> assert instance1 is not instance2

From the created instances, we can go back to the metaclasses:

.. code-block:: python

    >>> instance1.eClass
    <EClass name="MyMetaclass">

Then, we can add metaproperties to the freshly created metaclass:

.. code-block:: python

    >>> instance1.eClass.eAttributes
    []
    >>> MyMetaclass.eStructuralFeatures.append(Ecore.EAttribute('name', Ecore.EString))
    >>> instance1.eClass.eStructuralFeatures
    [<pyecore.ecore.EAttribute object at 0x7f7da72ba940>]
    >>> str(instance1.name)
    'None'
    >>> instance1.name = 'mystuff'
    >>> instance1.name
    'mystuff'

We can also create a new metaclass ``B`` and a new metareferences towards
``B``:

.. code-block:: python

    >>> B = Ecore.EClass('B')
    >>> MyMetaclass.eStructuralFeatures.append(Ecore.EReference('toB', B, containment=True))
    >>> b1 = B()
    >>> instance1.toB = b1
    >>> instance1.toB
    <pyecore.ecore.B object at 0x7f7da70531d0>
    >>> b1.eContainer() is instance1   # because 'toB' is a containment reference
    True

Opposite and 'collection' meta-references are also managed:

.. code-block:: python

    >>> C = Ecore.EClass('C')
    >>> C.eStructuralFeatures.append(Ecore.EReference('toMy', MyMetaclass))
    >>> MyMetaclass.eStructuralFeatures.append(Ecore.EReference('toCs', C, upper=-1, eOpposite=C.eStructuralFeatures[0]))
    >>> instance1.toCs
    []
    >>> c1 = C()
    >>> c1.toMy = instance1
    >>> instance1.toCs  # 'toCs' should contain 'c1' because 'toMy' is opposite relation of 'toCs'
    [<pyecore.ecore.C object at 0x7f7da7053390>]


Static Metamodels
=================

The static definition of a metamodel using PyEcore mostly relies on the
classical classes definitions in Python:

.. code-block:: python

    $ cat example.py
    """
    static metamodel example
    """
    from pyecore.ecore import EObject, EAttribute, EReference, EString, MetaEClass

    nsURI = 'http://example/1.0'


    class B(EObject, metaclass=MetaEClass):
        def __init__(self):
            pass


    class C(EObject, metaclass=MetaEClass):
        def __init__(self):
            pass


    class MyMetaclass(EObject, metaclass=MetaEClass):
        name = EAttribute(eType=EString)
        toB = EReference(eType=B, containment=True)
        toCs = EReference(eType=C, upper=-1)

        def __init__(self):
            pass

    # We need to update C in order to add the opposite meta-reference
    # At the moment, the information need to be added in two places
    C.toMy = EReference('toMy', MyMetaclass, eOpposite=MyMetaclass.toCs)
    C.eClass.eStructuralFeatures.append(C.toMy)

    $ python
    ...
    >>> import example
    >>> instance1 = example.MyMetaclass()
    >>> c1 = C()
    >>> c1.toMy = instance1
    >>> assert c1 is instance1.toCs[0] and c1.toMy is instance1


Importing an Existing XMI Metamodel/Model
=========================================

XMI support is still a work in progress, but the XMI import is on good tracks.
Currently, only basic XMI metamodel (``.ecore``) and model instances can be
loaded:

.. code-block:: python

    >>> from pyecore.resources import ResourceSet, URI
    >>> rset = ResourceSet()
    >>> resource = rset.get_resource(URI('path/to/mm.ecore'))
    >>> mm_root = resource.contents[0]
    >>> rset.metamodel_registry[mm_root.nsURI] = mm_root
    >>> # At this point, the .ecore is loaded in the 'rset' as a metamodel
    >>> resource = rset.get_resource(URI('path/to/instance.xmi'))
    >>> model_root = resource.contents[0]
    >>> # At this point, the model instance is loaded!

The ``ResourceSet/Resource/URI`` will evolve in the future. At the moment, only
basic operations are enabled: ``create_resource/get_resource/load/save...``.

Exporting an Existing XMI Resource
==================================

As for the XMI import, the XMI export (serialization) is still somehow very
basic. Here is an example of how you could save your objects in a file:

.. code-block:: python

    >>> # we suppose we have an already existing model in 'root'
    >>> from pyecore.resources.xmi import XMIResource
    >>> from pyecore.resources import URI
    >>> resource = XMIResource(URI('my/path.xmi'))
    >>> resource.append(root)  # We add the root to the resource
    >>> resource.save()  # will save the result in 'my/path.xmi'
    >>> resource.save(output='test/path.xmi'  # save the result in 'test/path.xmi'


You can also use a ``ResourceSet`` to deal with this:

.. code-block:: python

    >>> # we suppose we have an already existing model in 'root'
    >>> from pyecore.resources import ResourceSet, URI
    >>> rset = ResourceSet()
    >>> resource = rset.create_resource(URI('my/path.xmi'))
    >>> resource.append(root)
    >>> resource.save()


Installation
============

At the moment, the library is not on `pypi`, it will be added when the XMI
deserialization/serialization will be working. At the moment, the installation
must be performed manually (better in a virtualenv):

.. code-block:: bash

    $ python setup.py install

Dependencies
============

The dependencies required by pyecore are:

* ordered-set which is used for the ``ordered`` and ``unique`` collections expressed in the metamodel,
* lxml which is used for the XMI parsing.


Run the Tests
=============

Tests uses `py.test` and 'coverage'. Everything is driven by `Tox`, so in order
to run the tests simply run:

.. code-block:: bash

    $ tox


Liberty Regarding the Java EMF Implementation
=============================================

There is some meta-property that are not still coded inside PyEcore. More will
come with time.

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
* Eclipse XMI import (partially)
* Eclipse XMI export (partially).

The XMI import/export are still in an early stage of developement: no cross
resources references, not able to resolve file path uris and stuffs.

The things that are in the roadmap:

* documentation,
* code generator for the static part,
* EOperations support (static is ok, but not the dynamic metamodel, not in a proper way),
* object deletion,
* notification/Event system,
* command system (?).


Existing Projects
=================

There is not so much projects proposing to handle model and metamodel in Python.
The only projects I found are:

* PyEMOF (http://www.lifl.fr/~marvie/software/pyemof.html)
* EMF4CPP (https://github.com/catedrasaes-umu/emf4cpp)

PyEMOF proposes an implementation of the OMG's EMOF in Python. The project
targets Python2 and supports XMI import/export. The project didn't move since
2005, but seems quite complete.

EMF4CPP proposes a C++ implementation of EMF. This implementation also
introduces Python scripts to call the generated C++ code from a Python
environment.
