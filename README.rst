=======
PyEcore
=======
-----------------------------------------------------------
A Pythonic Implementation of the Eclipse Modeling Framework
-----------------------------------------------------------

PyEcore is a "Pythonic?" (sounds pretentious) implementation of EMF/Ecore for
Python3. It's purpose is to handle model/metamodels in Python almost the same
way the Java version does.

However, PyEcore enables you to use a simple ``instance.attribute`` notation
instead of ``instance.setAttribute(...)/getAttribute(...)`` for the Java
version. To achieve this, PyEcore relies on reflection (a lot).

Let see by yourself how it works on a very simple metamodel created on
the fly (dynamic metamodel)::

    >>> from pyecore.ecore import EClass, EAttribute, EString, EObject
    >>> A = EClass('A') # We create metaclass named 'A'
    >>> A.eAttributes.append(EAttribute('myname', EString, default_value='new_name')) # We add a name attribute to the A metaclass
    >>> a1 = A()
    >>> a1.myname
    'new_name'
    >>> a1.myname = 'a_instance'
    >>> a1.myname
    'a_instance'
    >>> isinstance(a1, EObject)
    True

PyEcore also support introspection::

    >>> a1.eClass # some introspection
    <EClass name="A">
    >>> a1.eClass.eClass
    <EClass name="EClass">
    >>> a1.eClass.eClass is a1.eClass.eClass.eClass
    True
    >>> a1.eClass.eStructuralFeatures
    (<pyecore.ecore.EAttribute at 0x7f6bf6cd91d0>,)
    >>> a1.eClass.eAttributes[0].name
    'myname'
    >>> a1.eClass.eAttributes[0].eClass
    <EClass name="EAttribute">

Runtime type checking is also performed (regarding what you expressed in your)
metamodel::

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

In order to create a new metaclass, you need to create an ``EClass`` instance::

    >>> import pyecore.ecore as Ecore
    >>> MyMetaclass = Ecore.EClass('MyMetaclass')

You can then create instances of your metaclass::

    >>> instance1 = MyMetaclass()
    >>> instance2 = MyMetaclass()
    >>> assert instance1 is not instance2

From the created instances, we can go back to the metaclasses::

    >>> instance1.eClass
    <EClass name="MyMetaclass">

Then, we can add metaproperties to the freshly created metaclass::

    >>> instance1.eClass.eAttributes
    []
    >>> MyMetaclass.eAttributes.append(Ecore.EAttribute('name', Ecore.EString))
    >>> instance1.eClass.eAttributes
    [<pyecore.ecore.EAttribute object at 0x7f7da72ba940>]
    >>> str(instance1.name)
    'None'
    >>> instance1.name = 'mystuff'
    >>> instance1.name
    'mystuff'

We can also create a new metaclass ``B`` and a new metareferences towards ``B``::

    >>> B = Ecore.EClass('B')
    >>> MyMetaclass.eReferences.append(Ecore.EReference('toB', B, containment=True))
    >>> b1 = B()
    >>> instance1.toB = b1
    >>> instance1.toB
    <pyecore.ecore.B object at 0x7f7da70531d0>
    >>> b1.eContainer() is instance1   # because 'toB' is a containment reference
    True

Opposite and 'collection' meta-references are also managed::

    >>> C = Ecore.EClass('C')
    >>> C.eReferences.append(Ecore.EReference('toMy', MyMetaclass))
    >>> MyMetaclass.eReferences.append(Ecore.EReference('toCs', C, upper=-1, eOpposite=C.eReferences[0]))
    >>> instance1.toCs
    []
    >>> c1 = C()
    >>> c1.toMy = instance1
    >>> instance1.toCs  # 'toCs' should contain 'c1' because 'toMy' is opposite relation of 'toCs'
    [<pyecore.ecore.C object at 0x7f7da7053390>]


Static Metamodels
=================

The static definition of a metamodel using PyEcore mostly relies on the
classical classes definitions in Python::

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
    C.eClass.eReferences.append(C.toMy)

    $ python
    ...
    >>> import example
    >>> instance1 = example.MyMetaclass()
    >>> c1 = C()
    >>> c1.toMy = instance1
    >>> assert c1 is instance1.toCs[0] and c1.toMy is instance1


Liberty Regarding the Java EMF Implementation
=============================================

There is some meta-property that are not still coded inside PyEcore. More will
come with time. At the moment, there is a slighlty difference between the
default Java EMF implementation and PyEcore:

* the ``eReferences`` and ``eAttributes`` meta-references are not derived, the ``eStructuralFeatures`` meta-reference is (in Java EMF, this is the opposite)


State
=====

In the current state, the project implements:

* the dynamic/static metamodel definitions,
* inheritance,
* enumerations,
* abstract metaclasses,
* runtime typechecking,
* attribute/reference creations,
* collections (attribute/references with upper bound set to ``-1``),
* reference eopposite,
* containment reference,
* introspection,
* select/reject on collections.

The things that are in the roadmap:

* documentation,
* Eclipse XMI import/export (the hard part),
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
