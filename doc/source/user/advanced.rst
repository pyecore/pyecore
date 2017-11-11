.. _advanced:

Advanced Usage
==============


.. _behavior:
Adding Behavior: Executable Models
----------------------------------

Using the Python dynamic nature, PyEcore allows you to add any kind of behavior
to your metamodel that will be launch on your model instance. You can add to
any metamodel, static **and** dynamic metamodel new behavior. The added
behavior can be the implementation of an ``EOperation`` defined in your
metamodel or a new operation. Also, as PyEcore allows you to dynamically
add new attributes to your class/metaclasses, you have the ability to add
information that are not directly defined in your metamodel.

For Static and Dynamic Metamodels
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The way of adding a new behavior to your ``EClass`` is pretty forward. This
example shows how to do it on a dynamic metamodel built on-the-fly:

.. code-block:: python

    from pyecore.ecore import EClass, EAttribute
    import pyecore.behavior as behavior # We need to import the 'behavior' package

    HelloWorld = EClass('HelloWorld')
    HelloWorld.eStructuralFeatures.append(EAttribute('name', EString))

    @HelloWorld.behavior
    def greeting(self):
        print('Hello World and', self.name)


If we sum up, the ``behavior`` is imported and a new ``EClass`` defined.
To this new ``EClass``, we added the ``greeting`` behavior. You can see that
the behavior addition is made directly using the ``EClass`` through the
``@HelloWorld.behavior`` annotation.

Now that our behavior is implemented, we can build an example model and launch
it:

.. code-block:: python

    a = A()
    a.name = 'guys'
    a.greeting()
    # prints 'Hello World and guys'


The exact same process can be applied to static metamodel. Considering that
we have a generated metamodel named ``hello``, the previous code becomes:

.. code-block:: python

    import pyecore.behavior as behavior
    import hello

    @hello.HelloWorld.behavior
    def greeting(self):
        print('Hello World and', self.name)


That's all, the model creation/execution remains the same. The interesting
thing about this is when you read your model from an XMI, your behavior is
automatically added to your model. Also, using closure, you can conditionally
inject a behavior or another to a model element, to sum up, you can dynamically
change your model behavior if you need.

**Caution:** if you only need to add a single behavior on static metamodel,
a prefered solution is to use the mixin generation proposed by ``pyecoregen``.
The mixin generation propose a strong and solid way of adding a dedicated
behavior to your metamodel.


For Dynamic Metamodels Read from an Ecore File
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

With the same flexibility, you can add behavior to your existing ``.ecore``. To
ease all of this, you can make use of the ``DynamicEPackage`` helper. Here is
an example of how to use it. We consider that we have an existing
``hello.ecore`` file, with the same metamodel than before:

.. code-block:: python

    from pyecore.resources import ResourceSet, URI
    from pyecore.utils import DynamicEPackage
    import pyecore.behavior as behavior

    # Read the metamodel first
    rset = ResourceSet()
    mm_root = rset.get_resource(URI('hello.ecore')).contents[0]

    # Register the metamodel (in case we open an XMI model later)
    rset.metamodel_registry[mm_root.nsURI] = mm_root

    # Get the metamodel helper
    hello = DynamicEPackage(mm_root)

    @hello.HelloWorld.behavior
    def greeting(self):
        print('Hello World and', self.name)


That's it. Beside the metamodel loading, the good stuff is always the same than
before. You can then either create instances or load an XMI model, and run your
model. Assuming we have a ``model.xmi`` file:

.. code-block:: python

    model_root = rset.get_resource(URI('model.xmi')).contents[0]
    model_root.greeting()


Defining an Entry Point to your Executable Model
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the previous section, we saw that it becomes possible to add behavior to
your metamodel and launch it by calling the one of the defined behavior.
However, this implies a knowledge of the added behavior in order to run the
adequat one. PyEcore provides a way of defining the main entry point of your
model. Currently, this entry point must be added to your root metaclass (i.e:
the ``EClass`` that will provide the root of your model). The following
example takes the same previous ``HelloWorld`` example, and add the entry
point:

.. code-block:: python

    @behavior.main
    @hello.HelloWorld.behavior
    def entry_point(self):
        self.greeting()


The entry point is defined by the ``@beavior.main`` annotation on a function.
This function must also be marked as a ``behavior``. One you've defined an
entry point, you can use the ``run()`` method from the ``pyecore.behavior``
module to run your executable model:

.. code-block:: python

    # We obtain the model from an XMI
    model_root = rset.get_resource(URI('model.xmi')).contents[0]
    behavior.run(model_root)


**Note:** the entry point can be defined with required or optional parameters:

.. code-block:: python

    @behavior.main
    @hello.HelloWorld.behavior
    def entry_point(self, i, x=None):
        print('Run', i, x)
        self.greeting()

    model_root = rset.get_resource(URI('model.xmi')).contents[0]
    behavior.run(model_root, 5, x='test')


Example
~~~~~~~

As full coded, ready to use, and explained example, check out the
:ref:`FSM` example.


Modifying Elements Using Commands
---------------------------------

PyEcore objects can be modified as shown previously, using basic Python
operators, but these mofifications cannot be undone. To do so, it is required to
use ``Command`` and a ``CommandStack``. Each command represent a basic action
that can be performed on an element (set/add/remove/move/delete):

.. code-block:: python

    >>> from pyecore.commands import Set
    >>> # we assume have a metamodel with an A EClass that owns a 'name' feature
    >>> a = A()
    >>> set = Set(owner=a, feature='name', value='myname')
    >>> if set.can_execute:
    ...     set.execute()
    >>> a.name
    myname

If you use a simple command withtout ``CommandStack``, the ``can_execute`` call
is mandatory! It performs some prior computation before the actual command
execution. Each executed command also supports 'undo' and 'redo':

.. code-block:: python

    >>> if set.can_undo:
    ...     set.undo()
    >>> assert a.name is None
    >>> set.redo()
    >>> assert a.name == 'myname'

As for the ``execute()`` method, the ``can_undo`` call must be done before
calling the ``undo()`` method. However, there is no ``can_redo``, the ``redo()``
call can be mad right away after an undo.

To compose all of these commands, a ``Compound`` can be used. Basically, a
``Compound`` acts as a list with extra methods (``execute``, ``undo``,
``redo``...):

.. code-block:: python

    >>> from pyecore.commands import Compound
    >>> a = A()  # we use a new A instance
    >>> c = Compound(Set(owner=a, feature='name', value='myname'),
    ...              Set(owner=a, feature='name', value='myname2'))
    >>> len(c)
    2
    >>> if c.can_execute:
    ...     c.execute()
    >>> a.name
    myname2
    >>> if c.can_undo:
    ...     c.undo()
    >>> assert a.name is None

In order to organize and keep a stack of each played command, a ``CommandStack``
can be used:

.. code-block:: python

    >>> from pyecore.commands import CommandStack
    >>> a = A()
    >>> stack = CommandStack()
    >>> stack.execute(Set(owner=a, feature='name', value='myname'))
    >>> stack.execute(Set(owner=a, feature='name', value='myname2'))
    >>> stack.undo()
    >>> assert a.name == 'myname'
    >>> stack.redo()
    >>> assert a.name == 'myname2'


Here is a quick review of each command:

* ``Set`` --> sets a ``feature`` to a ``value`` for an ``owner``
* ``Add`` --> adds a ``value`` object to a ``feature`` collection from an ``owner`` object (``Add(owner=a, feature='collection', value=b)``). This command can also add a ``value`` at a dedicated ``index`` (``Add(owner=a, feature='collection', value=b, index=0)``)
* ``Remove`` --> removes a ``value`` object from a ``feature`` collection from an ``owner`` (``Remove(owner=a, feature='collection', value=b)``). This command can also remove an object located at an ``index`` (``Remove(owner=a, feature='collection', index=0)``)
* ``Move`` --> moves a ``value`` to a ``to_index`` position inside a ``feature`` collection (``Move(owner=a, feature='collection', value=b, to_index=1)``). This command can also move an element from a ``from_index`` to a ``to_index`` in a collection (``Move(owner=a, feature='collection', from_index=0, to_index=1)``)
* ``Delete`` --> deletes an elements and its contained elements (``Delete(owner=a)``)


Creating Your own URI
---------------------

PyEcore uses ``URI`` to deal with 'stream' opening/reading/writing/closing.
An ``URI`` is used to give a file-like object to a ``Resource``. By default,
the basic ``URI`` provides a way to read and write to files on your system (if
the path used is a file system path, abstract paths or logical ones are not
serialized onto the disk). Another, ``HttpURI`` opens a file-like object from
a remote URL, but does not give the ability to write to a remote URL.

As example, in this section, we will create a ``StringURI`` that gives the
resource the ability to read/write from/to a Python String.

.. code-block:: python

    class StringURI(URI):
    def __init__(self, uri, text=None):
        super(StringURI, self).__init__(uri)
        if text is not None:
            self.__stream = StringIO(text)

    def getvalue(self):
        return self.__stream.getvalue()

    def create_instream(self):
        return self.__stream

    def create_outstream(self):
        self.__stream = StringIO()
        return self.__stream


The ``StringURI`` class inherits from ``URI``, and adds a new parameter to the
constructor: ``text``. In this class, the ``__stream`` attribute is handled in
the ``URI`` base class, and inherited from it.

The constructor builds a new ``StringIO`` instance if a text is passed to this
``URI``. This parameter is used when a string must be decoded.  In this context,
the ``create_instream()`` method is used to provide the ``__stream`` to read
from. In this case, it only returns the stream created in the constructor.

The ``create_outstream()`` methods is used to create the output stream. In this
case, a simple ``StringIO`` instance is created.

In complement, the ``getvalue()`` method provides a way of getting the result
of the load/save operation. The following code illustrate how the ``StringURI``
can be used:

.. code-block:: python

    # we have a model in memory in 'root'
    uri = StringURI('myuri')
    resource = rset.create_resource(uri)
    resource.append(root)
    resource.save()
    print(uri.getvalue())  # we get the result of the serialization

    mystr = uri.getvalue()  # we assume this is a new string
    uri = StringURI('newuri', text=mystr)
    resource = rset.create_resource(uri)
    resource.load()
    root = resource.contents[0]  # we get the root of the loaded resource

Dynamically Extending PyEcore Base Classes
------------------------------------------

PyEcore is extensible and there is two ways of modifying it: either by extending
the basic concepts (as ``EClass``, ``EStructuralFeature``...), or by directly
modifying the same concepts.

Extending PyEcore Base Classes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To extend the PyEcore base classes, the only thing to do is to create new
``EClass`` instances that have some base classes as ``superclass``.
The following excerpt shows how you can create an ``EClass`` instance that
will add support ``EAnnotation`` to each created instance:

.. code-block:: python

    >>> from pyecore.ecore import *
    >>> A = EClass('A', superclass=(EModelElement.eClass))  # we need to use '.eClass' to stay in the PyEcore EClass instance level
    >>> a = A()  # we create an instance that has 'eAnnotations' support
    >>> a.eAnnotations
    EOrderedSet()
    >>> annotation = EAnnotation(source='testSource')
    >>> annotation.details['mykey'] = 33
    >>> a.eAnnotations.append(annotation)
    >>> EOrderedSet([<pyecore.ecore.EAnnotation object at 0x7fb860a99f28>])

If you want to extend ``EClass``, the process is mainly the same, but there is a
twist:

.. code-block:: python

    >>> from pyecore.ecore import *
    >>> NewEClass = EClass('NewEClass', superclass=(EClass.eClass))  # NewEClass is an EClass instance and an EClass
    >>> A = NewEClass('A')  # here is the twist, currently, EClass instance MUST be named
    >>> a = A()  # we can create 'A' instance
    >>> a
    <pyecore.ecore.A at 0x7fb85b6c06d8>


Modifying PyEcore Base Classes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

PyEcore let you dynamically add new features to the base class and thus
introduce new feature for base classes instances:

.. code-block:: python

    >>> from pyecore.ecore import *
    >>> EClass.new_feature = EAttribute('new_feature', EInt)  # EClass has now a new EInt feature
    >>> A = EClass('A')
    >>> A.new_feature
    0
    >>> A.new_feature = 5
    >>> A.new_feature
    5

Deep Journey Inside PyEcore
---------------------------

This section will provide some explanation of how PyEcore works.

EClasse Instances as Factories
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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


Static/Dynamic ``EOperation``, Behind the Scene
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
    ...     print(self, param1)
    ...
    >>> A.python_class.myoperation = myoperation

To be able to propose a dynamic empty implementation of the operation, PyEcore
relies on Python code generation at runtime.
