pygen - Generate code from Ecore models
=======================================

If you have a meta-model represented as an instance of Pyecore, you can use this generator to
produce static code from it. The package currently consists of these parts:

* ``generator.py`` and ``formatter.py`` form a basic framework that can be put on top of any
  template-based code-generator that produce single-file outputs (like Jinja or Cheetah) in order to
  manage outputting multiple files in a certain folder structure. These modules are independent of
  Jinja and Pyecore.
* ``jinja.py`` refines the generic classes to be used with Jinja2 as file generator.
* ``ecore.py`` applies the Jinja2-based generator to create Pyecore Python classes from an Ecore
  meta model instantiated with Pyecore.

All modules except ``ecore.py`` should be moved into a separate distribution on PyPI to make it
available also outside of Pyecore.


Using the Ecore generator
-------------------------

The generator assumes reasonable defaults, so using it is straightforward. Assuming you load an
Ecore model with Pyecore like this:

.. code-block:: python

    rset = ResourceSet()
    resource = rset.get_resource(URI('library.ecore'))
    library_model = resource.contents[0]
    rset.metamodel_registry[library_model.nsURI] = library_model

Now ``library_model`` holds the root package of the loaded meta-model. From this instance the
corresponding Python classes are generated like this:

.. code-block:: python

    generator = EcoreGenerator()
    generator.generate(library_model, 'output-folder')

After this the ``output-folder`` will contain the generated package files, in this case a sub-folder
``library`` that can be directly imported into using Python code. Note that the generated classes
obviously depend on the Pyecore infrastructure to work. Follow the general documentation on how to
use static model classes in your application.


The pygen framework
-------------------

The modules ``generator``, ``formatter`` and ``jinja`` are generic and not limited to be used with
Pyecore. The overall design follows a very simple workflow pattern.

The ``Generator`` base class controls sets up and runs the worklow. The different steps of a
generation workflow are modeled as instances of base class ``Task``. A concrete generator will
override the empty ``tasks`` collection of the base class to set up the tasks to be executed
sequentially. The following is how the Pyecore generator does this:

.. code-block:: python

    class EcoreGenerator(JinjaGenerator):
        """Generation of static ecore model classes."""

        tasks = [
            EcorePackageInitTask(formatter=format_autopep8),
            EcorePackageModuleTask(formatter=format_autopep8),
        ]

        ...

In this example ``EcoreGenerator`` defines a generator workflow consisting of two tasks:

* ``EcorePackageInitTask`` generates the ``__init__.py`` file for a model package.
* ``EcorePackageModuleTask`` generates the corresponding module Python file.

The code also shows specific generator and task classes being instantiated here. The inheritance
"trees" are simple linear lines. The generator inheritance chain looks like this (from general to
specific):

1. ``generator.Generator``: base class offering a method to generate files into a target folder from
   any kind of model. The model is not limited to Pyecore, but could be anything, like dictionaries
   or lists as well. The generate method implementation realizes the core workflow by calling all
   tasks of contained in its ``tasks`` attribute.
2. ``generator.TemplateGenerator``: adds a static attribute to specify a relative path to the
   directory where input templates can be found.
3. ``jinja.JinjaGenerator``: configures the Jinja2 environment, which specifies all kinds of options
   for the code generation with Jinja.
4. ``ecore.EcoreGenerator``: the concrete generator translating Pyecore models into Python code with
   Jinja2 as code generator.

This hierarchy allows for customization at al levels: If you want to generate text from models, but
without templates, because it can be somehow hardcoded, derive directly from ``Generator``. If you
want to use a templating engine, but not Jinja2, derive from ``TemplateGenerator``. If you indeed
want to use Jinja2, but not generate files from Pyecore models, or use completely different
templates, derive from ``JinjaGenerator``. Deriving from ``EcoreGenerator`` may be useful in some
cases, but this class does provide Jinja2 filters and tests that are required by the used template
files. So the class is rather specific but of course can be used as a template when writing your
own concrete generator, e.g. to generate SQL from model.

Tasks also add functionality incrementally to support reuse and customization:

1. ``generator.Task``: base class for all generator tasks. It supports the generator workflow by
   exposing a ``run`` method that in turn calls various abstract methods to be implemented in
   derived classes. The class defines an API required to generate output files in a certain
   target directory. It exposes a model element filter to select the elements to execute this
   task for. Optionally, the constructor accepts a ``formatter`` argument, which has to be a
   callable, converting raw text generator output into whatever nicely formatted form you choose.
   The Pyecore generation tasks for instance are being passed ``formatter.format_autopep8``.
2. ``generator.TemplateFileTask``: adds a (relative) path to the template to be used and API to
   pass context data to the template.
3. ``jinja.JinjaTask``: holds the actual calls to Jinja2 to generate textual output and optionally
   applies the configured formatter. It uses the context passed in from the calling generator to
   pass data to the templates.
4. ``ecore.EcoreTask``: implements the model element filter by finding all elements of a certain
   Ecore type. It also determines file and folder names from those.

The two derived Ecore task classes mentioned in the above example are the leafs of the inheritance
line, implementing the remaining abstract methods depending on the concrete template being used.
They also provide additional context information to the template in use.

Both, generators and tasks pass configuration data in different stages:

* Static (class) attributes and instance attributes are used for configuration parameters that are
  specific for a certain *type* of generator.
* Parameters that affect how a specific *run* of the generator translates a particular model are
  passed as function arguments to the various workflow methods (like ``generate`` or ``run``).
