Changelog
---------

0.5.11
++++++

**Bugfixes**

- Add missing ``iD`` feature for ``EAttribute``. In EMF, the ``iD`` feature can
  be se for ``EAttribute``. This attribute was missing from the pyecore
  metamodel. This new version also adds the ``iD`` keyword for the
  ``EAttribute`` constructor.

- Add missing basic ``EDataType``. The added ``EDataTypes`` are:
    * ``EDate``,
    * ``EBigDecimal``,
    * ``EBooleanObject``,
    * ``ELongObject``,
    * ``EByte``,
    * ``EByteObject``,
    * ``EByteArray``,
    * ``EChar``,
    * ``ECharacterObject``,
    * ``EShort``,
    * ``EJavaClass``.
    

0.5.9/0.5.10
++++++++++++

**Bugfixes**

- Fix decoding issue when HttpURI with http-href is used. When a href is used,
  the ResourceSet resolver tries to concatenate the path built from the main uri
  resource and the href uri fragment. In the case of HttpURI, the concatenation
  provided a 'http://abc/http://cde' like uri. The ``normalize()`` method of URI
  was spliting on '://' and used unpacking to two vars exactly. With this kind
  of uri, it resulted in an exception. This commit fixes this issue using simply
  the ``maxsplit`` option from the ``split()`` method.

- Fix issue when ``name`` feature was called as part of descriptor. This error was
  simple, the ``name`` feature defined as a static meta-attribute of the
  ``ENamedElement`` metaclass was overriding the property implementation in the
  ``EStructuralFeature``. This issue was also preventing from properly monkey
  patching pyecore for ``name`` access.

0.5.8
+++++

**Bugfixes**

- Fix issue when multiple undo/redo are performed. Each time an undo is
  performed, the command stack top pointer is decremented. It only points to the
  command before the last one. Obviously, each time a redo is performed, the
  command stack needs to be incremented, and it points to the previously undone
  command. The 'redo' method was missing the top stack incrementation.


0.5.7
+++++

**Bugfixes**

- Fix default value for ``EAttribute``. ``EAttribute`` let the ability to express
  default values. This value is assigned when an ``EClass`` instance is created.
  The ``default_value`` is computed as follow: if the ``EAttribute``'s
  ``default_value`` is set, this ``default_value`` is returned. If the
  default_value of the ``Eattribute`` is not set, then the ``default_value`` of
  the ``EAttribute`` associated EDataType is set. This way of computing elements
  was not properly used during instance initialization.

**Miscellaneous**

- Fix some examples in the ``README.rst``.

0.5.6
+++++

**Features**

- Add missing ``EDataType`` management in the Acceleo generator.


**Miscellaneous**

- Add missing data type conversion for ``EDataType``.
- Fix once and for all the ``setup.py`` (hopefully).

0.5.5
+++++

**Bugfixes**

- Fix ``__update()`` method in ``EClass`` when many elements are added at once.
  This case occurs when ``append()`` is used on an ``EClass`` in order to add
  many ``EStructuralFeature``.

- Fix shared content for mutable ``EDataType``. When mutable EDatataypes are
  defined (e.g: ``EStringToStringMapEntry``), each default value was pointing to
  the same shared value (exactly the same thing that when ``def x(self, n={})``).
  The default_value is now computed, if a special attribute is set, the default
  value is always created as a new empty value.

- Fix default value for property instances accessed after the instance creation.


**Miscellaneous**

- Add missing ``EFeatureMapEntry``.
- Add missing LICENCE file in dist package.
- Add default value managmeent for 'instanceClass' derived datatypes.

0.5.0
+++++

**Features**

- Add new static metamodel generator (`@moltob <https://github.com/moltob>`_
  contribution, thanks!). The generator, named `pyecoregen <https://github.com/pyecore/pyecoregen>`_,
  is written in full Python/Jinja2 using `pymultigen <https://github.com/moltob/pymultigen>`_ a
  framework for multiple files generation. The generator usage is prefered over
  the MTL/Acceleo one as it can be launched from the command line directly and
  does not requires Java or Java-dependencies to run. The generated code is
  also automatically formatted using the ``autopep8`` project.

- Add EMF command support. The EMF command support gives the ability to represent
  actions that modify the model as single or composed modification command. There
  is 5 existing commands:
  * Set,
  * Add,
  * Remove,
  * Delete,
  * Compound.

  Each command affects the model in a certain way. The main advantage of using
  commands over direct modification is the fact that each of these commands can
  be undo/redo.

- Add Command Stack support. The Command stack gives the ability to easily schedule
  the execution of each commands. It also gives a simpler access to the undo/redo
  function of each commands and ensure that they are played/re-played in the
  right order.


**Bugfixes**

- Fix handling of 'non-required' parameters for ``EOperations``. When a
  parameter is set as 'non-required', the Python translation must consider that
  the parameter is defined as an optional named parameter.

- Fix issue with the computation of some internal properties for the ``delete()``
  method (the ``_inverse_rels`` set). The current algorithm keep track of each
  inverse relationships, and when an element is removed, the old record is
  deleted while a new one is added to the record set. The bug was affecting the
  registration of the new record during the deletion of the old one.

- Fix ``__update()`` method in ``EClass`` when an object deletion occurs. The
  update method deals with notifications to add/remove elements on the fly from
  the listened notification. When a REMOVE was notified, the wrong notification
  property was accessed resulting in a ``NoneTypeError`` exception.


**Miscellaneous**

- Add ``getEAnnotation()`` method on ``EModelElement``.
- Change 'getargspec' by 'getfullargspec' as it seems that 'getargspec' is
  deprecated since Python 3.0 and replaced by 'getfullargspec'.
- Add some performance improvements.
- Add missing ``pop()`` operation for ``EList/EBag``.
- Monkey patch ``insert()/pop()`` methods in ``OrderedSet``.
- Add missing ``@staticmethod`` when required.
- Add missing ``*args`` and ``**kwargs`` to the meta-instance creation in
  ``EClass``. This addition allows the user to create it's own '__init__' method
  for dynamic metaclasses using some trickery.


0.3.0
+++++

**Features**

- Add new class to ease dynamic metamodel handling. The dynamic metamodel
  manipulation is a little bit cumbersome when it comes to extract all the
  existing EClass from a loaded EPackage. A new class is provided:
  'DynamicEPackage' which constructs, using reflection, an object that has
  direct references to each EClass/sub-EPackage by name. This greatly helps the
  user to easily call and get EClass from a freshly loaded dynamic EPackage.


**Bugfixes**

- Fix missing double notification raised for eopposite references. When an
  eopposite reference were set, the notification system were called three times:
  one for the main feature (the feature on which the add/remove/set/unset have
  been made by the user) and two for the eopposite. The first eopposite
  notification were normal, but the second one was a residual notification sent
  by the algorithm. This new commit simply removes the extra-notifications and
  adds new tests to detect these issues.


**Miscellaneous**

- Add better semantic differentiation for ``EBag`` and ``ESet`` collections.
- Add slicing support for ``EList``.
- Add missing ``ordered`` and ``unique`` parameters for ``EAttribute``.


0.2.0
+++++

**Features**

- Add new static metamodel code generator (@moltob contribution, thanks!). The
  new generator gives more flexibility to the user as it allows the direct
  assignment of attributes/references values from the constructor. The feature
  reduces the amount of LOC required to create a fully initialized instance and
  also helps for the instance creation as IDE smart-completion feature can
  propose the attributes/references to the user.

**Miscellaneous**

- Fix some PEP8/Pylint refactoring and docstrings.
- Small performance improvement in the ``EcoreUtils.isinstance``.


0.1.5
+++++

**Bugfixes**

- Fix missing types from Ecore (@moltob contribution, thanks!). These types are
  the `E*Object` types for numbers. The modification had been done in the
  ``ecore.py`` file as these are default Ecore types and not XML types (or
  coming from another EMF lib). This commit increases the compatibility with
  existing ``.ecore`` files.


0.1.4
+++++

**Features**

- Add support for object deletion in PyEcore. The delete feature allows the user
  to remove parts of the model. Those parts can be a simple element or a sub-graph
  if a container object is deleted. The delete tries to keep up to date a special
  list that gathers the non-inverse navigable relation. When called, the method
  gathers all the EReferences of the object to delete and these special relations.
  It then update the pointed references. There is a special behavior if the object
  to delete is a proxy. If unresolved, the proxy can only be removed from the
  main location, but not from the remote one. If resolved, the proxy keep the
  classical behavior. This behavior tries to match the EMF-Java one: https://www.eclipse.org/forums/index.php/t/127567/

**Bugfixes**

- Fix double resources loading in same ``ResourceSet``. When two ``get_resource(...)``
  call with the same URI as parameter were done in the same ``ResourceSet``,
  two different resources were returned. The new behavior ensure that once the
  resource had been loaded, a second call to ``get_resource(...)`` with the
  same URI will return the resource created in the first place.

**Miscellaneous**

- Make use of ``ChainMap`` for ``global_registry`` management (simplify code).
- Raise a better exception when a 'broken' proxy is resolved.
- Add small performances improvement.


0.1.3
+++++

**Features**

- Add support for object proxies. The PyEcore proxy works a little bit differently from the Java EMF proxy, once
  the proxy is resolved, the proxy is not removed but is used a a transparent
  proxy (at the moment) and is not an issue anymore for type checking. Proxies are
  used for cross-document references.

- Remove resource-less objects from XMI serialization. This is a first step
  towards objects removal. The added behavior allows the user to "remove"
  elements in a way. If an element is not contained in a resource anymore, the
  reference towards the object is not serialized. This way, anytime an object is
  removed from a container and let 'in the void', XMI serialization will get rid
  of it. However, this new addition requires that the Ecore metamodel is always
  loaded in the global_registry (in case someone wants to serialize ecore files)
  as a metamodel can references basic types (EString, EBoolean) which are
  basically not contained in a resource.

**Bugfixes**

- Fix bug on EStructuralFeature owner assignment when EClass is updated.

0.1.2
+++++

**Bugfixes**

- Only the default ``to_string`` method on EDataType was called, even if a new
  one was passed as parameter. The issue was a simple typo in the ``__init__``
  method.

- The EBoolean EDataType was missing a dedicated ``to_string`` method. This
  issue introduced a 'desync' between XMI that EMF Java can read and PyEcore.
  In cas of EBoolean, the serialized value was either ``True`` or ``False``
  which is not understood by Java (only ``true`` or ``false``, lower case).


0.1.1
+++++

**Features**

- Improved performances on big files deserialization (2x faster). This new
  version relies on descriptor instead of ``__getattribute__/__setattr__``.
  The code is not more compact, but more clear and split.

- New static metamodel generator, producing code related to this new version.

- Add XML type transtyping in the static metamodel generator.


**Bugfixes**

- When an ``eOpposite`` feature was set on an element, the actual opposite
  reference ``eOpposite`` was not updated.

- Subpackages managements for the static metamodel generator. The
  ``eSubpackages`` and ``eSuperPackage`` variables were not placed in the
  package, but in the module.


**Miscellaneous**

- Update bad examples in the README.rst


0.0.10-3
++++++++

**Project State**

- First full working version
