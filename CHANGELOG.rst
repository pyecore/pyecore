Changelog
---------

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
