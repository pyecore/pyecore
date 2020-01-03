.. _quickstart:

Quick Start
===========

Quick Overview
--------------

PyEcore is a "Pythonic" implementation of EMF/Ecore for Python 3.
Its purpose is to handle model/metamodels in Python almost the same
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
    EOrderedSet([<EStructuralFeature myname: EString(str)>])
    >>> a1.eClass.eStructuralFeatures[0].name
    'myname'
    >>> a1.eClass.eStructuralFeatures[0].eClass
    <EClass name="EAttribute">
    >>> a1.__getattribute__('myname')
    'a_instance'
    >>> a1.__setattr__('myname', 'reflexive')
    >>> a1.__getattribute__('myname')
    'reflexive'
    >>> a1.eSet('myname', 'newname')
    >>> a1.eGet('myname')
    'newname'

Runtime type checking is also performed, based on what is defined in the metamodel:

.. code-block:: python

    >>> a1.myname = 1
    Traceback (most recent call last):
        File "<stdin>", line 1, in <module>
        File ".../pyecore/ecore.py", line 66, in setattr
            raise BadValueError(got=value, expected=estruct.eType)
    pyecore.ecore.BadValueError: Expected type EString(str), but got type int with value 1 instead


PyEcore supports static and dynamic metamodels.  These are described
in the next sections.

Navigating in a Model
---------------------

When you have a model loaded in memory, either loaded from a resource (XMI,
JSON) or built programmatically, you can navigate from a point to another using
the name of the meta-attributes/references using their names (as despicted in
the quickstart). This way, you can get attributes and references values
directly.

Moreover, for containment references, there is another way of getting the
contained elements. You can use the reference name, but you can also use the
``eContents`` reference that keep tracks of all the elements that are directly
contained by another. Let consider the following simple metaclass and
some instances:

.. code-block:: python

    from pyecore.ecore import EClass, EReference

    A = EClass('A')
    A.eStructuralFeatures.append(EReference('container1', containment=True,
                                            eType=A, upper=-1))
    A.eStructuralFeatures.append(EReference('container2', containment=True,
                                            eType=A, upper=-1))

    # we create an element hierarchy which looks like this:
    # +- a1
    #   +- a2    (in container1)
    #     +- a4  (in container1)
    #   +- a3    (in container2)
    a1, a2, a3, a4 = A(), A(), A(), A()
    a1.container1.append(a2)
    a2.container1.append(a4)
    a1.container2.append(a3)


You can get the children of ``a1`` using ``a1.container1`` and
``a1.container2``, or you can get all the children directly contained by ``a1``
like this:

.. code-block:: python

    a1.eContents  # returns a list containing a2 and a3


You can also get all the children contained in an element, transitively, using
the ``eAllContents()`` method that returns a generator over all the children:

.. code-block:: python

    # this will print repr for a2, a4 and a3
    for child in a1.eAllContents():
        print(child)


Dynamic Metamodels
------------------

Dynamic metamodels provide the ability to create metamodels "on-the-fly". You
can create metaclass hierarchy, add ``EAttribute`` and ``EReference``.

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
    >>> MyMetaclass.eStructuralFeatures.append(Ecore.EAttribute('name', Ecore.EString))  # Add 'name' attribute, of type string
    >>> instance1.eClass.eAttributes  # Is there a new feature?
    [<pyecore.ecore.EAttribute object at 0x7f7da72ba940>]  # Yep, the new feature is here!
    >>> str(instance1.name)  # There is a default value for the new attribute
    'None'
    >>> instance1.name = 'mystuff'
    >>> instance1.name
    'mystuff'
    >>> # Now the feature name may be used as a keyword argument in the constructor
    >>> instance3 = MyMetaclass(name='myname')
    >>> instance3.name
    'myname'

We can also create a new metaclass ``B`` and a new meta-reference to ``B``:

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

Explore Dynamic metamodel/model objects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is possible, when you are handling an object in the Python console, to ask
for all the meta-attributes/meta-references and meta-operations that can
be called on it using ``dir()``.  This will work with either a dynamic metamodel
object or a model instance. This allows you to quickly experiment and find the
information you are looking for:

.. code-block:: python

    >>> A = EClass('A')
    >>> dir(A)
    ['abstract',
     'delete',
     'eAllContents',
     'eAllOperations',
     'eAllReferences',
     'eAllStructuralFeatures',
     'eAllSuperTypes',
     'eAnnotations',
     'eAttributes',
     'eContainer',
     # <snip ... many more >
     'findEOperation',
     'findEStructuralFeature',
     'getEAnnotation',
     'instanceClassName',
     'interface',
     'name']
    >>> a = A()
    >>> dir(a)
    []
    >>> A.eStructuralFeatures.append(EAttribute('myname', EString))
    >>> dir(a)
    ['myname']


Enhance the Dynamic metamodel
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Even if you define or use a dynamic metamodel, you can add dedicated methods
(e.g: ``__repr__``) to the equivalent Python class. Each ``EClass`` instance is
linked to a Python class which can be reached using the ``python_class`` field:

.. code-block:: python

    >>> A = EClass('A')
    >>> A.python_class
    pyecore.ecore.A

You can directly add new "non-metamodel" methods to this class:

.. code-block:: python

    >>> a = A()
    >>> a
    <pyecore.ecore.A at 0x7f4f0839b7b8>
    >>> A.python_class.__repr__ = lambda self: 'My repr for real'
    >>> a
    My repr for real


Static Metamodels
-----------------

The static definition of a metamodel using PyEcore mostly relies on the
classical class definitions in Python. Each Python class is linked to an
``EClass`` instance and has a special metaclass. The static code for metamodel
also provides a model layer and the ability to easily refer/navigate inside the
defined meta-layer.

.. code-block:: python

    # 'library' directory content
    # +- library
    #  `- __init__.py library.py

    # 'library/library.py' content
    # ... stuffs here
    class Writer(EObject, metaclass=MetaEClass):
        name = EAttribute(eType=EString)
        books = EReference(upper=-1)

        def __init__(self, name=None, books=None, **kwargs):
            if kwargs:
                raise AttributeError('unexpected arguments: {}'.format(kwargs))

            super().__init__()
            if name is not None:
                self.name = name
            if books:
                self.books.extend(books)
    # ... Other stuff here

    # Session example
    >>> import library
    >>> # we can create elements and handle the model level
    >>> smith = library.Writer(name='smith')
    >>> book1 = library.Book(title='Ye Old Book1')
    >>> book1.pages = 100
    >>> smith.books.append(book1)
    >>> assert book1 in smith.books
    >>> assert smith in book1.authors
    >>> # ...
    >>> # We can also navigate the meta-level
    >>> import pyecore.ecore as Ecore  # import the Ecore metamodel for tests
    >>> assert isinstance(library.Book.authors, Ecore.EReference)
    >>> library.Book.authors.upperBound
    -1
    >>> assert isinstance(library.Writer.name, Ecore.EAttribute)


There are two main ways of creating static ``EClass`` with PyEcore. The first
one relies on code generation while the second one uses manual
definition.

The code generator defines a Python package hierarchy instead of
just a Python module. This allows more freedom for dedicated operations and
references between packages.

How to Generate the Static Metamodel Code
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The static code is generated from an ``.ecore`` where your metamodel is defined
(the EMF ``.genmodel`` files are not yet supported (probably in future version).

There are currently two ways of generating the code for your metamodel. The first
one is to use a MTL generator (in ``/generator``) and the second one is to use a
dedicated command line tool written in Python, using Pymultigen, Jinja and PyEcore.

Using the Acceleo/MTL Generator
""""""""""""""""""""""""""""""
**Note:** the Acceleo generator is deprecated.  Use of pyecoregen is now prefered.

To use this generator, you need Eclipse and the right Acceleo plugins. Once
Eclipse is installed with the right plugins, you need to create a new Acceleo
project, copy the  PyEcore generator in it, configure a new Acceleo runner,
select your ``.ecore`` and your good to go. There is plenty of documentation
on Internet for Acceleo/MTL project creation and management.



Using the Dedicated CLI Generator (PyEcoregen)
""""""""""""""""""""""""""""""""""""""""""""""

For more complex metamodels and more robust generation, pyecoregen is better,
and is the recommended solution for the static metamodel code generation.
Advantages (over Acceleo) include:

* Provides a simple command line interface
* Provides the cability to perform generation programmatically
* Provides a framework for code generation WITHIN PyEcore
* Allows you to code dedicated behavior in mixin classes,
* Much simpler installation, with all dependencies, using `pip`.

This generator source code can be found at this address with mode details:
https://github.com/pyecore/pyecoregen and is available on Pypi, so you can
install it using:

.. code-block:: bash

    $ pip install pyecoregen

This will automatically install all the required dependencies and give you a new
CLI tool: ``pyecoregen``.

Using this tool, your static code generation is very simple:

.. code-block:: bash

    $ pyecoregen -e your_ecore_file.ecore -o your_output_path

Once the code is generated, you can import it and use it in your Python code.


Manually define static ``EClass``
""""""""""""""""""""""""""""""""""

To manually define static ``EClass``, simply create a Python class, and
add the ``@EMetaclass`` class decorator. This decorator adds the right
metaclass to the defined class, and introduces any missing classes in its
inheritance tree. Defining a simple metaclass can be done like:

.. code-block:: python

    @EMetaclass
    class Person(object):
        name = EAttribute(eType=EString)
        age = EAttribute(eType=EInt)
        children = EReference(upper=-1, containment=True)

        def __init__(self, name):
            self.name = name

    # As the relation is reflexive, it must be set AFTER metaclass creation
    Person.children.eType = Person

    p1 = Person('Parent')
    p1.children.append(Person('Child'))


Without more information, all the created metaclasses will be added to a default
``EPackage``, generated automatically. If the ``EPackage`` must be controlled, a
global variable of ``EPackage`` type, named ``eClass``, must be created in the
module.

.. code-block:: python

    eClass = EPackage(name='pack', nsURI='http://pack/1.0', nsPrefix='pack')

    @EMetaclass
    class TestMeta(object):
        pass

    assert TestMeta.eClass.ePackage is eClass

However, when ``@EMetaclass`` is used and the newly created metaclass
inherits from a non metaclass (see the example below), the ``super()``
call in the ``__init__`` constructor cannot be directly called. Instead,
``super(x, self)`` must be called:

.. code-block:: python

    class Stuff(object):
        def __init__(self):
            self.stuff = 10


    @EMetaclass
    class A(Stuff):
        def __init__(self, tmp):
            super(A, self).__init__()
            self.tmp = tmp


    a = A()
    assert a.stuff == 10

If you want to directly extends the PyEcore metamodel, the ``@EMetaclass`` is
not required, and ``super()`` can be used.

.. code-block:: python

    class MyNamedElement(ENamedElement):
        def __init__(self, tmp=None, **kwargs):
            super().__init__(**kwargs)
            self.tmp = tmp


Ask for all created instances of an EClass
-----------------------------------------

PyEcore keeps track of all created instances. You can then ask for the created
instances of a particular type using the ``allInstances()`` method on
a metaclass. The result is a generator that contains all the instances of the
right type:

.. code-block:: python

    from pyecore.ecore import EClass

    # Find all the instances of an EClass
    for x in EClass.allInstances():
        print(x)

    # Create an EClass instance and some instances of this new metaclass
    A = EClass('A')

    a1 = A()
    a2 = A()
    a3 = A()

    print(list(A.allInstances())    # displays 3 instances

    del a1
    print(list(A.allInstances())    # displays 2 instances


As all the created elements are returned, when multiple resources
are loaded it can be difficult sometimes to only filter elements from dedicated
resources. The ``allInstances()`` method takes an optional argument:
``resources`` which let you specify which resources should be searched
for instances.

.. code-block:: python

    from pyecore.ecore import EClass
    from pyecore.resources import ResourceSet

    # We will create an EClass instance and some instance of this new metaclass
    A = EClass('A')

    a1 = A()
    a2 = A()
    a3 = A()

    # We distribute each instance in a different resources
    rset = ResourceSet()
    resource1 = rset.create_resource('http://virtual1')
    resource2 = rset.create_resource('http://virtual2')
    resource3 = rset.create_resource('http://virtual3')

    resource1.append(a1)
    resource2.append(a2)
    resource3.append(a3)

    print(list(A.allInstances(resources=(resource1, resource2))))  # a1 and a2
    print(list(A.allInstances(resources=(resource3,))))  # a3



Programmatically Create a Metamodel and Serialize it
----------------------------------------------------

Creating a metamodel programmatically is the same as creating a dynamic
metamodel. You create ``EClass`` instances, add ``EAttributes`` and
``EReferences`` to them, and add the instances in an ``EPackage``. For example
here is a little snippet that creates two metaclasses and adds them to the
an ``EPackage`` instance:

.. code-block:: python

    from pyecore.ecore import *

    # Define a Root that can contain A and B instances,
    # B instances can hold references towards A instances
    Root = EClass('Root')
    A = EClass('A')
    B = EClass('B')
    A.eStructuralFeatures.append(EAttribute('name', EString))
    B.eStructuralFeatures.append(EReference('to_many_a', A, upper=-1))
    Root.eStructuralFeatures.append(EReference('a_container', A, containment=True))
    Root.eStructuralFeatures.append(EReference('b_container', B, contaimnent=True))

    # Add all the concepts to an EPackage
    my_ecore_schema = EPackage('my_ecor', nsURI='http://myecore/1.0', nsPrefix='myecore')
    my_ecore_schema.eClassifiers.extend([Root, A, B])


Then, in order to serialize it, it is simply a matter of adding the created
``EPackage`` to a ``Resource`` (more details about ``Resource`` are provided in
the sections `Importing an Existing XMI Metamodel/Model`_,  `Exporting an
Existing XMI Resource`_ and `Dealing with JSON Resources`_). Here is an
example of how the created metamodel could be serialized in an XMI format:

.. code-block:: python

    from pyecore.resources import ResourceSet, URI

    rset = ResourceSet()
    resource = rset.create_resource(URI('my/location/my_ecore_schema.ecore'))  # This will create an XMI resource
    resource.append(my_ecore_schema)  # we add the EPackage instance in the resource
    resource.save()  # we then serialize it

This process is identical to the one you would apply for serializing almost any
kind of model.


Notifications
-------------

PyEcore gives you the ability to listen to modifications performed on an
element. The ``EObserver`` class provides a basic observer which can receive
notifications from an ``EObject``.  It is registered like:

.. code-block:: python

    >>> import library as lib  # we use the wikipedia library example
    >>> from pyecore.notification import EObserver, Kind
    >>> smith = lib.Writer()
    >>> b1 = lib.Book()
    >>> observer = EObserver(smith, notifyChanged=lambda x: print(x))
    >>> b1.authors.append(smith)  # observer receive the notification from smith because 'authors' is eOpposite or 'books'

The ``EObserver`` notification method can be set using a function (or lambda, as shown)
or by class inheritance:

.. code-block:: python

    >>> def print_notif(notification):
    ...     print(notification)
    ...
    >>> observer = EObserver()
    >>> observer.observe(b1)
    >>> observer.notifyChanged = print_notif
    >>> b1.authors.append(smith)  # observer receive the notification from b1

Using inheritance:

.. code-block:: python

    >>> class PrintNotification(EObserver):
    ...     def __init__(self, notifier=None):
    ...         super().__init__(notifier=notifier)
    ...
    ...     def notifyChanged(self, notification):
    ...         print(notification)
    ...
    ...
    >>> observer = PrintNotification(b1)
    >>> b1.authors.append(smith)  # observer receive the notification from b1

The ``Notification`` object contains information about the performed
modification:

* ``new`` -> the new added value (can be a collection) or ``None`` is remove or unset
* ``old`` -> the replaced value (always ``None`` for collections)
* ``feature`` -> the ``EStructuralFeature`` modified
* ``notifier`` -> the object that has been modified
* ``kind`` -> the kind of modification performed

``kind`` is one of:

* ``ADD`` ->  an object is added to a collection
* ``ADD_MANY`` -> multiple objects are added to a collection
* ``REMOVE`` -> an object is removed from a collection
* ``SET`` -> a value is set in an attribute/reference
* ``UNSET`` -> a value is removed from an attribute/reference


Importing an Existing XMI Metamodel/Model
-----------------------------------------

XMI support is still a little rough on the edges, but the XMI import is on good tracks.
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


Dynamic Metamodel Helper
~~~~~~~~~~~~~~~~~~~~~~~~~

Once a metamodel is loaded from an XMI metamodel (from a ``.ecore`` file), the
metamodel root that is gathered is an ``EPackage`` instance. To access each
``EClass`` from the loaded resource, a ``getEClassifier(...)`` call must be
performed:

.. code-block:: python

    >>> #...
    >>> resource = rset.get_resource(URI('path/to/mm.ecore'))
    >>> mm_root = resource.contents[0]
    >>> A = mm_root.getEClassifier('A')
    >>> a_instance = A()

When a big metamodel is loaded, this operation can be cumbersome. To ease this
operation, PyEcore proposes a helper that gives a quick access to each
``EClass`` contained in the ``EPackage`` and its subpackages. This helper is the
``DynamicEPackage`` class. This shows a typical usage:

.. code-block:: python

    >>> #...
    >>> resource = rset.get_resource(URI('path/to/mm.ecore'))
    >>> mm_root = resource.contents[0]
    >>> from pyecore.utils import DynamicEPackage
    >>> MyMetamodel = DynamicEPackage(mm_root)  # We create a DynamicEPackage for the loaded root
    >>> a_instance = MyMetamodel.A()
    >>> b_instance = MyMetamodel.B()


Adding External Metamodel Resources
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

External resources for metamodel loading should be added in the resource set.
For example, for resources using XMLType instead of the Ecore one,
the following datatypes could be created first by hand that way:

.. code-block:: python

    int_conversion = lambda x: int(x)  # translating str to int durint load()
    String = Ecore.EDataType('String', str)
    Double = Ecore.EDataType('Double', int, 0, from_string=int_conversion)
    Int = Ecore.EDataType('Int', int, from_string=int_conversion)
    IntObject = Ecore.EDataType('IntObject', int, None,
                                from_string=int_conversion)
    Boolean = Ecore.EDataType('Boolean', bool, False,
                              from_string=lambda x: x in ['True', 'true'],
                              to_string=lambda x: str(x).lower())
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

Please note that in the case of XMLTypes, an implementation is provided with
PyEcore and it is not required to create those types by hand. These types are
only used here to highlight how new resources could be added from scratch.
To see how to use the XMLTypes, see sections below.

Metamodel References by 'File Path'
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


If a metamodel references other metamodels in a 'file path' manner, PyEcore requires
that the REFERENCED metamodel be loaded first and registered against the
metamodel path URI.

.. code-block:: python

    >>> # Suppose that metamodel A.ecore has references to B.ecore as '../../B.ecore'.
    >>> # Path of A.ecore is 'a/b/A.ecore' and B.ecore is '.'
    >>> resource = rset.get_resource(URI('B.ecore'))      # Load B.ecore first
    >>> root = resource.contents[0]
    >>> rset.metamodel_registry['../../B.ecore'] = root   # Register 'B' metamodel at 'file path' uri
    >>> resource = rset.get_resource(URI('a/b/A.ecore'))  # A.ecore now loads


Adding External resources
~~~~~~~~~~~~~~~~~~~~~~~~~

When a model references another one, they both need to be added to the same
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
----------------------------------

As with XMI import, support for XMI export (serialization) is still somewhat
basic. Here is an example of how you could save your objects in a file:

.. code-block:: python

    >>> # we suppose we have an already existing model in 'root'
    >>> from pyecore.resources.xmi import XMIResource
    >>> from pyecore.resources import URI
    >>> resource = XMIResource(URI('my/path.xmi'))
    >>> resource.append(root)  # We add the root to the resource
    >>> resource.save()  # will save the result in 'my/path.xmi'
    >>> resource.save(output=URI('test/path.xmi'))  # save the result in 'test/path.xmi'


You can also use a ``ResourceSet``:

.. code-block:: python

    >>> # we suppose we have an already existing model in 'root'
    >>> from pyecore.resources import ResourceSet, URI
    >>> rset = ResourceSet()
    >>> resource = rset.create_resource(URI('my/path.xmi'))
    >>> resource.append(root)
    >>> resource.save()


Multiple Root XMI Resource
~~~~~~~~~~~~~~~~~~~~~~~~~~

PyEcore supports XMI resources with multiple roots. When deserialized, the
``contents`` attribute of the loaded ``Resource`` contains all the deserialized
roots (usually, only one is used). If you want to add a new root to your
resource, you only can simply use the ``append(...)`` method:

.. code-block:: python

    from pyecore.resources import ResourceSet, URI

    # we suppose we have already existing roots named 'root1' and 'root2'
    rset = ResourceSet()
    resource = rset.create_resource(URI('my/path.xmi'))
    resource.append(root1)
    resource.append(root2)
    resource.save()


Altering XMI ``xsi:type`` serialization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When an XMI resource is serialized, information about the type of each element
is inserted in the file. By default, the field ``xsi:type`` is used, but in some
cases, you could want to change this field name to ``xmi:type``. To perform such
a switch, you can pass an option to resource serialization.

.. code-block:: python

    from pyecore.resources.xmi import XMIOptions

    # ... with an 'XMIResource' in the 'resource' variable
    resource.save(options={XMIOptions.OPTION_USE_XMI_TYPE: True})

Using UUID to reference elements instead of URI fragments during serialization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the XMI resource, the elements are classicaly referenced using a URI
fragment. This fragment is built using the containment reference name and the
object position in the resource. If you load a model that contains UUIDs, the
XMI resource will automatically switch in "UUID mode" and you don't have to
do anything else.  During the next ``save()``, the resource will embed the
UUID of each element. However, if you build a resource from scratch, the
default behavior is to use the URI fragment. You can change this during the
resource creation, or after it has been created, with the ``use_uuid``  attribute.

This shows switching to "UUID mode" for an existing resource , created
using a ``ResourceSet``):

.. code-block:: python

    from pyecore.resources import ResourceSet

    # ... with 'root' set to the model we want to serialize
    rset = ResourceSet()
    resource = rset.create_resource(URI('my/path/output.xmi'))
    resource.use_uuid = True
    resource.append(root)  # we add the root to the resource
    resource.save()


The attribute ``use_uuid`` may also be set directly when creating an ``XMIResource``
when a ResourceSet is not needed.

.. code-block:: python

    from pyecore.resources.xmi import XMIResource

    # ... with 'root' set to the model we want to serialize
    resource = XMIResource(URI('my/path/output.xmi'), use_uuid=True)
    resource.append(root)
    resource.save()


Forcing default values serializations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When an XMI resource is serialized, default and ``None`` values are not written
in the file. You can alter this behavior by passing the
``XMIOptions.SERIALIZE_DEFAULT_VALUES`` option during the save operation.

.. code-block:: python

    from pyecore.resources.xmi import XMIOptions

    # ... with an 'XMIResource' in the 'resource' variable
    resource.save(options={ XMIOptions.SERIALIZE_DEFAULT_VALUES: True })

This option will also introduce a special XML node ``xsi:nil="true"`` when
an attribute or a reference is explicitly set to ``None``.


Mapping a URI to a different location/URI
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sometimes, it may be necessary to 'convert' a URI from the format found in the
XMI to a new one that is more easily understood. This is typically the case for
some Eclipse URIs that are part of the XMI resource
(eg: ``platform://eclipse.org/xxx/yyy``). PyEcore cannot resolve these, as it is
unaware of the Eclipse platform. The solution is to provide a mapping to allows
PyEcore how to translate the URIs appropriately.

.. code-block:: python

    # Given a resource 'foo.xmi' that references a metamodel
    # 'platform://eclipse.org/ecore/Ecore' with references to elements
    # like: 'platform://eclipse.org/ecore/Ecore#//A'
    # In addition, we have references to a resources like:
    # 'resources://COMMON/files/bar.xmi#//' with 'bar.xmi' in './files'
    # in our system.
    from pyecore.resources import ResourceSet

    rset = ResourceSet()

    # Here is the mapper setup
    rset.uri_mapper['platform://eclipse.org/ecore/Ecore'] = 'http://www.eclipse.org/emf/2002/Ecore'
    # or, alternatively,
    # rset.uri_mapper['platform://eclipse.org/ecore'] = 'http://www.eclipse.org/emf/2002'
    rset.uri_mapper['resources://COMMON'] = '.'

    # we then load the resource
    resource = rset.get_resource(URI('foo.xmi'))


  **Note* Object resolution is lazy in many cases, so the mapper
  setup can be made after resource loading.


Dealing with JSON Resources
---------------------------

PyEcore is also able to load/save JSON models/metamodels. The JSON format it uses
tries to be close to the one described in the `emfjson-jackson <https://github.com/emfjson/emfjson-jackson>`_ project.
The way the JSON serialization/deserialization works, is similar to XMI resources,
but the JSON resource factory is not loaded by default, and must be manually registered.
The registration can be performed globally or at a ``ResourceSet`` level.

Register the JSON resource factory for a given ``ResourceSet``.

.. code-block:: python

    >>> from pyecore.resources import ResourceSet
    >>> from pyecore.resources.json import JsonResource
    >>> rset = ResourceSet()  # We have a resource set
    >>> rset.resource_factory['json'] =   # we register the factory for '.json' extensions


Register the JSON resource factory globally.

.. code-block:: python

    >>> from pyecore.resources import ResourceSet
    >>> from pyecore.resources.json import JsonResource
    >>> ResourceSet.resource_factory['json'] = JsonResource


Once the factory is registered, loadind and saving models or metamodels in JSON
is done the same as for XMI. See the XMI section for examples load/save resources using a ``ResourceSet``.

**NOTE:** Currently, the Json serialization is performed using the default Python
``json`` lib, by first translating the PyEcore model to a ``dict`` before
export/import. For large models, this implies a memory and performance cost.



Deleting Elements
-----------------

Deleting elements in EMF has issues because of the special model "shape" that
can impact the deletion algorithm. PyEcore supports two ways of deleting elements.
One is a real deletion, while the other is less direct.

The ``delete()`` method
~~~~~~~~~~~~~~~~~~~~~~~

The first way of deleting element is to use the ``delete()`` method which is
owned by every ``EObject/EProxy``:

.. code-block:: python

    >>> # we suppose we have an already existing element in 'elem'
    >>> elem.delete()

This call is also recursive by default: every sub-object of the deleted element
is also deleted. This behavior is the one by default as a "containment"
reference is a strong constraint.

The behavior of the ``delete()`` method can be confusing when there are many
``EProxy`` instances. As the ``EProxy`` only gives a partial view of the
object while it is not resolved, the ``delete()`` can only correctly remove
resolved proxies. If a resource or elements that are referenced in many
other resources must be destroyed, the best solution is to resolve all the
proxies first, then to delete them.  This ensures that broken proxies are not
introduced.


Removing an element from its container
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can also remove elements from a model using XMI serialization. If you want
to remove an element from a Resource, you have to remove it from its container.
PyEcore does not serialize elements that are not contained by a ``Resource``, and
also does not serialize any references to elements that are not serialized.

Working with XMLTypes
---------------------

PyEcore provides a partial implementation of the XMLTypes. This implementation
is already shipped with PyEcore and can directly be used. This is typically done
by simply importing the package.

.. code-block:: python

    import pyecore.type as xmltypes

    # from this point, the metamodel is registered in the global registry
    # meaning it is not mandatory to register it manually in a ResourceSet


The current implementation is incomplete. Some derived attributes and collections
are still empty, but the main part of the metamodel is usable.

Traversing the Whole Model with Single Dispatch
-----------------------------------------------

Sometimes, you need to go across your whole model, and you want to have a
call a function for each element in the model. To achieve
this goal, PyEcore proposes a simple way of performing single dispatch which
is equivalent for dynamic and static metamodels. This is implemented using
Python's ``@functools.singledispatch``.

Here is an example using the `library <https://upload.wikimedia.org/wikipedia/commons/thumb/9/92/EMF_based_meta-model.png/800px-EMF_based_meta-model.png>`_
metamodel.

.. code-block:: python

    import library
    from pyecore.utils import dispatch

    class LibrarySwitch(object):
        @dispatch
        def do_switch(self, o):
            print('Fallback for objects of kind ', o.eClass.name)

        @do_switch.register(library.Writer)
        def writer_switch(self, o):
            print('Visiting a ', o.eClass.name, ' named ', o.name)

        @do_switch.register(library.Book)
        def book_switch(self, o):
            print('Reading a ', o.eClass.name, ' titled ', o.name)


    switch = LibrarySwitch()
    # assuming we have a Library instance in 'mylib'
    for obj in mylib.eAllContents():
        switch.do_switch(obj)


In this example, only the ``Writer`` and the ``Book`` metaclasses are dispatched
the other instances would fall in the default ``do_switch`` method. In the case
of inheritence, if a method for a dedicated metaclass is not found, ``dispatch``
will search for a method that has been registered for a super type of the instance.
So in the example model above, if there were ``library.Paperback``
that extended the ``library.Book`` metaclass, the ``book_switch`` method would still be
called, for ``Paperback`` instances since no method was registered explicitly for ``Paperback``.
