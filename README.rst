====================================================================
PyEcore: A Pythonic Implementation of the Eclipse Modeling Framework
====================================================================

|master-build| |license|

.. |master-build| image:: https://travis-ci.org/aranega/pyecore.svg?branch=master
    :target: https://travis-ci.org/aranega/pyecore

.. |develop-build| image:: https://travis-ci.org/aranega/pyecore.svg?branch=develop
    :target: https://travis-ci.org/aranega/pyecore

.. |license| image:: https://img.shields.io/badge/license-New%20BSD-blue.svg
    :target: https://raw.githubusercontent.com/aranega/pyecore/develop/LICENSE

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
    >>> A = EClass('A')  # We create metaclass named 'A'
    >>> A.eStructuralFeatures.append(EAttribute('myname', EString, default_value='new_name')) # We add a name attribute to the A metaclass
    >>> a1 = A()  # We create an instance
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
    >>> a1.eSet('myname', 'newname')
    >>> a1.eGet('myname')
    'newname'

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

.. contents:: :depth: 2

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
classical classes definitions in Python. The following example is more related
to a 'by hand' static metamodel definition. This way of producing metamodels is
kinda deprecated as a MTL generator (in ``/generator``) automatically produces a
static metamodel from the ``.ecore`` definition.

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


The automatic code generator defines a Python package hierarchie instead of
only a Python module. This allows more freedom for dedicated operations and
references between packages.


Static/Dynamic ``EOperation``
=============================

PyEcore also support ``EOperation`` definition for static and dynamic metamodel.
For static metamodel, the solution is simple, a simple method with the code is
added inside the defined class. The corresponding ``EOperation`` is created on
the fly. Theire is still some "requirements" for this. In order to be understood
as an ``EOperation`` candidate, the defined method must have at least one
parameter and the first parameter must always be named ``self``.

For dynamic metamodels, the simple fact of adding an ``EOperation`` instance in
the ``EClass`` instance, adds an "empty" implementation:

.. code-block:: python

    >>> import pyecore.ecore as Ecore
    >>> A = Ecore.EClass('A')
    >>> operation = Ecore.EOperation('myoperation')
    >>> param1 = Ecore.EParameter('param1', eType=Ecore.EString, required=True)
    >>> operation.eParameters.append(param1)
    >>> A.eOperations.append(operation)
    >>> a = A()
    >>> help(a.myoperation)
    Help on method myoperation:

    myoperation(param1) method of pyecore.ecore.A instance
    >>> a.myoperation('test')
    ...
    NotImplementedError: Method myoperation(param1) is not yet implemented

For each ``EParameter``, the ``required`` parameter express the fact that the
parameter is required or not in the produced operation:

.. code-block:: python

    >>> operation2 = Ecore.EOperation('myoperation2')
    >>> p1 = Ecore.EParameter('p1', eType=Ecore.EString)
    >>> operation2.eParameters.append(p1)
    >>> A.eOperations.append(operation2)
    >>> a = A()
    >>> a.operation2(p1='test')  # Will raise a NotImplementedError exception

You can then create an implementation for the eoperation and link it to the
EClass:

.. code-block:: python

    >>> def myoperation(self, param1):
    ...:    print(self, param1)
    ...:
    >>> A.python_class.myoperation = myoperation

To be able to propose a dynamic empty implementation of the operation, PyEcore
relies on Python code generation at runtime.


Notifications
=============

PyEcore gives you the ability to listen to modifications performed on an
element. The ``EObserver`` class provides a basic observer which can receive
notifications from the ``EObject`` it is register in:

.. code-block:: python

    >>> import library as lib  # we use the wikipedia library example
    >>> from pyecore.notification import EObserver, Kind
    >>> smith = lib.Writer()
    >>> b1 = lib.Book()
    >>> observer = EObserver(smith, notifyChanged=lambda x: print(x))
    >>> b1.authors.append(smith)  # observer receive the notification from smith because 'authors' is eOpposite or 'books'

The ``EObserver`` notification method can be set using a lambda as in the
previous example, using a regular function or by class inheritance:

.. code-block:: python

    >>> def print_notif(notification):
    ...:    print(notification)
    ...:
    >>> observer = EObserver()
    >>> observer.observe(b1)
    >>> observer.notifyChanged = print_notif
    >>> b1.authors.append(smith)  # observer receive the notification from b1

Using inheritance:

.. code-block:: python

    >>> class PrintNotification(EObserver):
    ...:    def __init__(self, notifier=None):
    ...:        super().__init__(notifier=notifier)
    ...:
    ...:    def notifyChanged(self, notification):
    ...:        print(notification)
    ...:
    ...:
    >>> observer = PrintNotification(b1)
    >>> b1.authors.append(smith)  # observer receive the notification from b1

The ``Notification`` object contains information about the performed
modification:

* ``new`` -> the new added value (can be a collection) or ``None`` is remove or unset
* ``old`` -> the replaced value (always ``None`` for collections)
* ``feature`` -> the ``EStructuralFeature`` modified
* ``notifer`` -> the object that have been modified
* ``kind`` -> the kind of modification performed

The different kind of notifications that can be currently received are:

* ``ADD`` -> when an object is added to a collection
* ``ADD_MANY`` -> when many objects are added to a collection
* ``REMOVE`` -> when an object is removed from a collection
* ``SET`` -> when a value is set in an attribute/reference
* ``UNSET`` -> when a value is removed from an attribute/reference


Deep Journey Inside PyEcore
===========================

This section will provide some explanation of how PyEcore works.

EClasse Instances as Factories
------------------------------

The most noticeable difference between PyEcore and Java-EMF implementation is
the fact that there is no factories (as you probably already seen). Each EClass
instance is in itself a factory. This allows you to do this kind of tricks:

.. code-block:: python

    >>> A = EClass('A')
    >>> eobject = A()  # We create an A instance
    >>> eobject.eClass
    <EClass name="A">
    >>> eobject2 = eobject.eClass()  # We create another A instance
    >>> assert isinstance(eobject2, eobject.__class__)
    >>> from pyecore.ecore import EcoreUtils
    >>> assert EcoreUtils.isinstance(eobject2, A)


In fact, each EClass instance create a new Python ``class`` named after the
EClass name and keep a strong relationship towards it. Moreover, EClass
implements is a ``callable`` and each time ``()`` is called on an EClass
instance, an instance of the associated Python ``class`` is created. Here is a
small example:

.. code-block:: python

    >>> MyClass = EClass('MyClass')  # We create an EClass instance
    >>> type(MyClass)
    pyecore.ecore.EClass
    >>> MyClass.python_class
    pyecore.ecore.MyClass
    >>> myclass_instance = MyClass()  # MyClass is callable, creates an instance of the 'python_class' class
    >>> myclass_instance
    <pyecore.ecore.MyClass at 0x7f64b697df98>
    >>> type(myclass_instance)
    pyecore.ecore.MyClass
    # We can access the EClass instance from the created instance and go back
    >>> myclass_instance.eClass
    <EClass name="MyClass">
    >>> assert myclass_instance.eClass.python_class is MyClass.python_class
    >>> assert myclass_instance.eClass.python_class.eClass is MyClass
    >>> assert myclass_instance.__class__ is MyClass.python_class
    >>> assert myclass_instance.__class__.eClass is MyClass
    >>> assert myclass_instance.__class__.eClass is myclass_instance.eClass


The Python class hierarchie (inheritance tree) associated to the EClass instance

.. code-block:: python

    >>> B = EClass('B')  # in complement, we create a new B metaclass
    >>> list(B.eAllSuperTypes())
    []
    >>> B.eSuperTypes.append(A)  # B inherits from A
    >>> list(B.eAllSuperTypes())
    {<EClass name="A">}
    >>> B.python_class.mro()
    [pyecore.ecore.B,
     pyecore.ecore.A,
     pyecore.ecore.EObject,
     pyecore.ecore.ENotifier,
     object]
    >>> b_instance = B()
    >>> assert isinstance(b_instance, A.python_class)
    >>> assert EcoreUtils.isinstance(b_instance, A)


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


Adding External Metamodel Resources
-----------------------------------

External resources for metamodel loading should be added in the resource set.
For example, some metamodels use the XMLType instead of the Ecore one.
The resource creation should be done by hand first:

.. code-block:: python

    int_conversion = lambda x: int(x)  # translating str to int durint load()
    String = Ecore.EDataType('String', str)
    Double = Ecore.EDataType('Double', int, 0, from_string=int_conversion)
    Int = Ecore.EDataType('Int', int, from_string=int_conversion)
    IntObject = Ecore.EDataType('IntObject', int, None,
                                from_string=int_conversion)
    Boolean = Ecore.EDataType('Boolean', bool, False,
                              from_string=lambda x: x in ['True', 'true'])
    Long = Ecore.EDataType('Long', int, 0, from_string=int_conversion)
    EJavaObject = Ecore.EDataType('EJavaObject', object)
    xmltype = Ecore.EPackage()
    xmltype.eClassifiers.extend([String,
                                 Double,
                                 Int,
                                 EJavaObject,
                                 Long,
                                 Boolean,
                                 IntObject])
    xmltype.nsURI = 'http://www.eclipse.org/emf/2003/XMLType'
    xmltype.nsPrefix = 'xmltype'
    xmltype.name = 'xmltype'
    rset.metamodel_registry[xmltype.nsURI] = xmltype

    # Then the resource can be loaded (here from an http address)
    resource = rset.get_resource(HttpURI('http://myadress.ecore'))
    root = resource.contents[0]


Adding External resources
-------------------------

When a model reference another one, they both need to be added inside the same
ResourceSet.

.. code-block:: python

    rset.get_resource(URI('uri/towards/my/first/resource'))
    resource = rset.get_resource(URI('uri/towards/my/secon/resource'))

If for some reason, you want to dynamically create the resource which is
required for XMI deserialization of another one, you need to create an empty
resource first:

.. code-block:: python

    # Other model is 'external_model'
    resource = rset.create_resource(URI('the/wanted/uri'))
    resource.append(external_model)


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
    >>> resource.save(output=URI('test/path.xmi'))  # save the result in 'test/path.xmi'


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

PyEcore is available on ``pypi``, you can simply install it using ``pip``:

.. code-block:: bash

    $ pip install pyecore

The installation can also be performed manually (better in a virtualenv):

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

* There is some meta-property that are not still coded inside PyEcore. More will come with time,
* ``Resource`` can only contain a single root at the moment,
* External resources (like ``http://www.eclipse.org/emf/2003/XMLType``) must be create by hand an loaded in the ``global_registry`` or as a ``resource`` of a ``ResourceSet``.

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
* Eclipse XMI import (partially),
* Eclipse XMI export (partially),
* simple notification/Event system,
* EOperations support,
* code generator for the static part.

The XMI import/export are still in an early stage of developement: no cross
resources references, not able to resolve file path uris and stuffs.

The things that are in the roadmap:

* EMF proxies
* object deletion,
* documentation,
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
