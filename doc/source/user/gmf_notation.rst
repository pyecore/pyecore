.. _gmfnotation:

GMF Notation Model for Python
=============================

This little tutorial shows "in depth" how to generate Python/PyEcore code for
the `GMF-Notation <http://www.eclipse.org/modeling/gmp/?project=gmf-notation>`_
metamodel using `pyecoregen <https://github.com/pyecore/pyecoregen>`_.

Generating the Metamodel Code
-----------------------------

First, due to some dependencies expressed in the GMF Notation ``.ecore`` (relative
paths towards other ``.ecore``), it is required to have the full GMF Notation
hierarchy as well as the EMF source code. Actually, only the folder hierarchy
and the ``.ecore`` contained in the different projects are required.

Using ``pyecoregen``, the code generation is really easy, and it is performed like
this (under Linux, but the process should be the same for Windows/MacOS):

.. code-block:: bash

  $ pyecoregen -e notation.ecore -o .

Here, we assume that the ``notation.ecore`` is in the current directory, and the
generated code will be set in the same directory.

Modifying the GMF Notation Metamodel Code
-----------------------------------------

Currently, there is a small restriction in PyEcore/pyecoregen that "forgot" to
add a metaclass for one of the generated ``EClass``. This case is very specific
and cannot be detected at the moment, so a manual modification is required.

The modification implies the addition of ``metaclass=MetaEClass`` at line 353:

.. code-block:: python

    # Before
    class View(EModelElement):

    # After
    class View(EModelElement, metaclass=MetaEClass):


You can now quickly try the generated code by popping a Python REPL:

.. code-block:: python

    >>> import notation
    >>> notation.Diagram()
    <notation.notation.Diagram at 0x7fd50aee55f8>
    >>> diag = notation.Diagram(name='my_diag')
    >>> diag.name
    'my_diag'


Adding Dedicated Behavior
-------------------------

The thing with the GMF Notation original project is that some names and
behaviors are  defined dynamically in the generated Java code. Consequently, in
order to match the serialization/deserialization behavior, it is required to
add the same behavior to the generated Python code.

First, there is some relations that are dynamically renamed in the code. Thus
``persistedChildren`` becomes ``children`` and ``persistedEdges`` becomes ``edges``.
This can be expressed in PyEcore with the following code:

.. code-block:: python

    import notation

    notation.View.persistedChildren.name = 'children'
    notation.View.children = notation.View.persistedChildren
    notation.Diagram.persistedEdges.name = 'edges'
    notation.Diagram.edges = notation.Diagram.persistedEdges


Then, if we must add a dedicated serialization/deserialization for the
``RelativeBendpointList`` datatype. On the original code, this datatype is a list
that contains many kind of ``BendPoint`` (this type is not expressed in the
metamodel, consequently, we need to add it manually).

.. code-block:: python

    class BendPoint(object):
        def __init__(self, source_x, source_y, target_x, target_y):
            self.source_x = source_x
            self.source_y = source_y
            self.target_x = target_x
            self.target_y = target_y

        def __repr__(self):
            return '[{}, {}, {}, {}]'.format(self.source_x, self.source_y,
                                             self.target_x, self.target_y)


Then, we must add a dedicated function that will be used for deserializing
a list of ``BendPoint``. If we look through a GMF Notation Model example, here
is how a list of ``BendPoint`` is serialized:

.. code-block:: xml

    <bendpoints ... points="[4, 0, 56, 53]$[4, -24, 56, 29]$[-62, -24, -10, 29]$[-62, -53, -10, 0]"/>


Each ``BendPoint`` is separated by a ``$``, and each number in between ``[...]``
represents the `source x, source y, target x, target y` coordinate. The function
that will take this string and create a list of ``BendPoint`` is the following:

.. code-block:: python

    def from_str(s):
        result = []
        for line in s.split('$'):
            v = [int(i) for i in line[1:-1].split(',')]
            result.append(BendPoint(v[0], v[1], v[2], v[3]))
        return result


And the code required for serializing an existing list of ``BendPoint`` is the
following:

.. code-block:: python

    def to_str(o):
        s = '{o!r}'.format(o=o)
        return s.replace('], [', ']$[')[1:-1]


Then, these function are registered as custom serializer/deserializer for the
``RelativeBendpointList`` datatype:

.. code-block:: python
    notation.RelativeBendpointList.from_string = from_str
    notation.RelativeBendpointList.to_string = to_str


Loading a GMF Notation Model
----------------------------

Loading an existing GMF Notation Model is then quite easy and uses the basic
PyEcore API:

.. code-block:: python

    from pyecore.resources import ResourceSet
    import notation

    # insert here the code with the custom serializer/deserializer...etc

    rset = ResourceSet()
    rset.metamodel_registry[notation.nsURI] = notation  # register the notation metamodel

    resource = rset.get_resource('my_notation_file.xmi')
    root = resource.contents[0]


Now, ``root`` contains the root of your GMF Notation model.

## Modifying a GMF Notation Model

You can now modify the model, add elements... using the default PyEcore API:

.. code-block:: python

    root.name = 'my_new_name' # Changing model name
    # ...


Saving the Modified Model
-------------------------

When you need to save your modified model. If your original model serializes
it's type using the ``xsi:type`` field and you want to keep the same behavior,
you need to add a dedicated option.

.. code-block:: python

    from pyecore.resources.xmi import XMIOptions

    options = {
        XMIOptions.OPTION_USE_XMI_TYPE: True
    }
    resource.save(options=options)


If you want to save your model in a different file, you can save the resource
this way instead:

.. code-block:: python

    options = {
        XMIOptions.OPTION_USE_XMI_TYPE: True
    }
    resource.save('my_other_file.xmi', options=options)


This way, your original model file will not be overridden.
