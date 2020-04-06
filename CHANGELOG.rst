Changelog
---------

0.11.4
++++++

**Bugfixes**

- Fix issue with xmi ecore supertype references. When an ecore model has two elements A and B and that B inheriths from
A which is another element in a second ecore model, then, as their name
are equivalent, the resolution could, sometimes have problems in
resolving the elements, mistaking A from the first ecore with A from the
second one. In the case the wrong ecore was referenced, it implied a
circular reference for inheritency that caused the ecore file loading to
fail.

- Fix issue with weird URI (``plateform:/``). Weird uri that does not contains ``://`` provoques problems in the
automatic object resolving. This fix avoid that the relative uri
computation adds the relative path to the external uri it tries to
resolve.

- Fix issue with computation of ``many`` feature. The "algo" used to compute the ``many`` feature was wrong and introduced non-logical behavior when a reference or an attribute was having its lower and upper bound set to a same value higher than ``0`` (e.g.: ``2..2``).Thanks
`@jorensips <https://github.com/jorensips>`_ for the issue.

0.11.3
++++++

**Bugfixes**

- Fix issue with ``None`` object serialization for containment features. This happened when a ``None`` is explicitly written in a containment reference and the ``XMIOptions`` for default value serialization is activated. In that case a special ``nil`` object was supposed to be written, but it was not the case here.


0.11.2
++++++

**Bugfixes**

- Fix change of container of an objet when the reference is single.
Thanks `@annighoefer  <https://github.com/annighoefer>`_ for the fix!
The issue came when an object was moved from a single relationship container to another one from the same class, the contained object was contained by the two containers.

- Fix Fix root element id not added to uuid_dict if its feature.ID is set.
Thanks `@ewoudwerkman <https://github.com/ewoudwerkman>`_ for the fix!
The root node's ``ID`` was not referenced in the ``uuid_dict`` even if the root node had the ``ID`` feature set.

0.11.1
++++++

**Bugfixes**

- Fix XMI serialization compatibility when a proxy to a metaclass is used (typically when a metamodel reference another).
Thanks `@stefanq <https://github.com/stefanq>`_ for the simple demo/example/test!


**Miscellaneous**

- Remove ``issubclass`` patch, the new version remove this requirement and still assure the same behavior.


0.11.0
++++++

**Features**

- Add an ``URIConverter`` to transform ``URIs`` to custom ones (Thanks
`@ewoudwerkman <https://github.com/ewoudwerkman>`_ for the issue and the
pull requests!).
Each new converter can be isolated by ``ResourceSet`` or globaly for every
``Resource``.

**Bugfixes**

- Fix empty valued id attributes to be used as keys in reference links when saving a resource (Thanks `@annighoefer  <https://github.com/annighoefer>`_!).

**Miscellaneous**

- Remove dependency on deprecated defusedxml.lxml



0.10.3
++++++

**Bugfixes**

- Fix EDate serialization (Thanks `@ewoudwerkman <https://github.com/ewoudwerkman>`_!).
This patch provides a solution to the issues with time zone information in dates.
It makes the parsing and serialization of dates compatible with how EMF currently
handles dates and UTC offsets.

- Fix xmi empty references refer to root (Thanks `@annighoefer  <https://github.com/annighoefer>`_!).
Deleted objects that were also referred by non-containment references elsewhere were serialized in xmi
as `ref=""`, introducing a `BadValueError` when loading the file again as the root of the model was found as reference.
The fix solves the loading issue by skiping empty references.



0.10.2
++++++

**Miscellaneous**

- Add custom JSON serializer support
 (Thanks `@rodriguez-facundo   <https://github.com/rodriguez-facundo>`_ and `@filippometacell   <https://github.com/filippometacell>`_!)
 This support is not yet documented and will perhaps never be.


0.10.1
++++++

**Bugfixes**

- Fix enumeration literal addition as attribute. In the case literals where
  added to an enumeration using the 'eLiterals' collection, this implied that
  the ``EEnum`` instance was not updated with the required instance attribute.
  This new implementation uses a listener to catch additions that are made to
  the enumeration in order to either add or remove instance attributes.

- Fix issue with XMI serialization for single element container. In those cases
  the path towards the object was not well serialized. It results in a false
  XMI path which made the produced XMI not usable with Eclipse EMF. (Thanks `@annighoefer  <https://github.com/annighoefer>`_!)

- Prevent ``id`` with spaces from being used. Spaces are used for separating
  multiple references to other objects. (Thanks `@annighoefer  <https://github.com/annighoefer>`_!)


**Miscellaneous**

- Improve error message for ``BadValueError`` exception.


0.10.0
++++++

**Features**

- Add first support for ``EGenerics``. This implementation is currently
  incomplete as it is not possible to express dedicated types for instances.
  This capability will be added in future versions. The current version is able
  to catch only a part of the generic semantic, but at least it does not
  prevent from opening files and models that uses them (it should not).

- Add new XMLType metamodel generation. This new version makes a better use
  of derived collections and fixes some oddities of the previous one.

- Add first implementation of ``allInstances()`` method on ``EClass`` instances.
  This implementation can still benefits from some optimizations. The
  ``allInstances()`` method is working by keeping track of all created PyEcore
  objects in a ``WeakSet``. This set is then crossed and each matching
  instances are returned as a generator.


**Bugfixes**

- Fix missing ``EGenericType`` features like ``eTypeParameter``. These
  attributes were missing from the Ecore metamodel leading to errors when
  ecore models using them were deserialized.

- Fix collection reaffectation. These kind of reaffectation (e.g:
  ``x.foo = y.bar``, where ``foo`` and ``bar`` are ``EStructuralFeature``
  instances) now raises and error. The previous implementation could cause
  side-effects which were hard to anticipate.

- Fix bad format for ``EDate``. The old format that were parsed and produced
  by PyEcore was not EMF-Java compatible. This new implementation is using the
  iso format which seems to be the one used by default by EMF.

**Miscellaneous**

- Add context manager to unpatch the ``issubclass`` builtin function.
- Add ``alias`` function to inject alias features that have reserved names.

0.9.0
+++++

**Features**

- Add URI mapper like support. This mapper allows you to map a new URI or an
  URI start that can be later resolved if required. The typical use case is When
  dealing with Eclipse XMI where there is some ``plateforme://xxx/yyy`` uri.

- Add ``iD`` attribute support for ``EAttribute`` in XMI serialization. This
  feature ensure that if an ``EAttribute`` is defined in an ``EClass`` with its
  ``iD`` attribute set to ``True``, then, this attribute value will be used in
  the XMI serialization in order to save the reference towards the element.
  However, if an ``xmi:id`` is set to the element, the reference will use this
  xmi id no matter what.

- Add safe compilation of generated ``EOperation`` using ``RestrictedPython``
  (Thanks `@CFAndy <https://github.com/CFAndy>`_). The compilation of generated
  method is now performed using a 'safe' context. Even is the current generated
  code does not use special methods or functions, in future version, it is
  planed that PyEcore will be able to fetch behaviors that could be directly
  added to the ``.ecore``.


**Bugfixes**

- Fix issue with resolved fragment in resource when loading it. This bug was
  affecting resources with crossrefs towards different resources but whith the
  same fragment (eg: ``my-uri1#//A`` and ``my-uri2#//A``). In this case, the
  first resolved fragment were always returned, even if it was said as part of
  another resource.

- Add missing registration of ``ELong`` datatype.

- Fix issue when an object is moved to another container. An issue was occuring
  when an object moved from a container to another container. Currently, the
  object properly saw that it moved to another container, but the container
  collection/attribute was not aware that the object migrated to another
  container.



**Miscellaneous**

- Use a common 'uuid format' for XMI resources (easily overrideable).
- Switch from 'collection' to 'collection.abc' for Python 3.7.
- Update documentation fixing missing ``eType`` in example.


0.8.8
+++++

**Bugfixes**

- Fix out of sync XMI/JSON serialization (Thanks `@CFAndy <https://github.com/CFAndy>`_).
  When multiple XMI/JSON are serialized at the end of a program, some files are
  not serialized properly. To avoid this behavior, a flush of the produced file
  is performed at the end of the ``save()`` method for each ``Resource``.

0.8.7
+++++

**Bugfixes**

- Fix Json resource deserialization for primitive collections (Thanks `@afonsobspinto <https://github.com/afonsobspinto>`_). The Json deserialization
  was always assuming that when a collection was found in the Json, it always
  was a collection of ``EObject`` whereas they could also be primitive values.

**Miscellaneous**

- Add some performance improvements in resources deserialization.


0.8.6
+++++

**Bugfixes**

- Fix issue with URI spliting during json deserialization.
- Fix issue with redundant attributes in json format (Thanks `@TerryKingston <https://github.com/TerryKingston>`_!).
  Having redundant attributes for opposite containment relationship in the json
  serialized resource introduced the installation of a new proxy instead of the
  proper object resolution.

**Miscellaneous**

- Add performances improvement in json deserialization.


0.8.5
+++++

**Bugfixes**

- Fix issue with the new version of the ``ordered-set`` dependency. The new
  version introduces a change in the way the sublist returned from a slices
  is managed. The fix proposed in PyEcore introduces a patch for the
  ``OrderedSet`` class that proposes the same behavior from the new version
  while letting the opportunity to change it when subclassing ``OrderedSet``.


0.8.4
+++++

**Bugfixes**

- Fix issue with empty strings in XMI for 'many' ``EAttribute``.

0.8.3
+++++

**Features**

- Add support for ``tag`` attributes in XMI.
- Add ``URI`` change support for ``Resource``.
- Add patch for ``issubclass`` so the test works regardless the input parameters
  are ``EClass`` instances or not.
- Add ``xsi:schemaLocation`` deserialization support.

**Bugfixes**

- Fix bad containment feature value for ``contents`` on ``EAnnotation``.
- Fix resource resolving for non-trivial ``URI``.
- Fix bad crossreferences serialization for "many" features (collections).
- Fix issue for strings serialization in 'many' ``EAttribute``. Issue where
  happening when whitespaces were in a String for 'many' ``EAttribute``.

0.8.2
+++++

**Bugfixes**

- Fixed ``many`` faulty computation in cases where ``upper == lower > 1``. This
  case is not very common, but it could occurs.
- Fixed missing deserialization for ``EDate`` datatype. The missing method on
  resulted in a bad ``str`` object conversion leading to an exception as the
  a ``datetime`` object was expected instead of a ``str``.

**Miscellaneous**

- Improve ``many`` derived attribute computation, resulting in performance
  improvements.
- Add performance improvement tweaks.
- Move ``dispatch`` from ``pyecore.dispatch`` to ``pyecore.utils``


0.8.1
+++++

**Features**

- Add ``dispatch`` decorator to mimic the ``doSwitch`` from EMF. This
  implementation relies on the use of the ``singleDispatch`` decorator and does
  not include a ``ComposedSwitch`` equivalent as some restrictions from EMF are
  no longer an issue in Python.


**Bugfixes**

- Fixed ``lower`` and ``upper`` derived attributes computation. The previous
  implementation were considering the attributes as normal ones instead of
  derived ones.

- Fixed merge issue during ``0.8.0`` release. A case test was not properly
  working, and models which have crossref towards models that were using
  UUID raised an exception.

**Miscellaneous**

- Improved performances of the ``many`` derived attribute.


0.8.0
+++++

**Features**

- Add first support for ``EDerivedCollection``. The derived collections are
  obtained from many features that are also marked as derived. A derived
  collection does not stores nor gets direct information, instead it fetches
  information from other collection, compute a result and store it. In the
  realisation, a derived collection will inherits from a generic derived
  collection that only proposed an empty implementation. Then, the
  implementation must be manually added.

- Add multi-root support for XMI and JSON resources. XMI and JSON with multiple
  roots can now be serialized and deserialized. Their handling is pretty
  transparent as the addition of a new root goes through the ``append(...)``
  method.

- Add a ``remove(...)`` method on resources. This method is pretty much the
  opposite of the ``append(...)`` method on resources, it simply remove a
  root from the resource.

**Bugfixes**

- Exception when a wrong type value was inserted in a reference for generated
  code. The call to the ``EcoreUtils.isinstance`` method were raising an
  exception as the last part of the code tries to deal with an unexisting
  methods from the generated class.

- Fix ``EProxy`` 'force resolve' for static metamodels. When a proxy is set
  towards a static metaclass, the proxy resolution tries to handle the
  inverse reference list which only exists in the ``.eClass`` "level".
  Consequently, when a static metaclass is used, the corresponding ``EClass``
  instance must be used.

**Miscellaneous**

- Add new module for basic values and collections. This module contains the
  ``ECollection`` and ``EValue`` classes. These class were formerly in the
  ``ecore`` module, but due to further development, it is better to have it
  into a dedicated place. This modification is retrocompatible and invisible
  for existing manual/generated code.


0.7.15/16
+++++++++
**Features**

- Add xmi option for default value serialization. This new option allows to
  save the default value in the produced XMI, and it also gives the ability to
  store attribute set to `None` as `xsi:nill="true"` field.


0.7.14
++++++
**Features**

-  Add href uuid (de)serialization for XMI. This new features allows the XMI
   for having href that directly uses the uuid of the target element.


**Bugfixes**

- Fix nsmap computation for heteroneous models with crossrefs. When crossrefs
  are serialized in XMI, they need to add the referenced namespace at the
  root of the XMI. This fix adds these namespace and their related prefixes.


0.7.13
++++++

**Bugfixes**

- Fix bad ``EAttribute`` decoding for XMI root element. By default, each field
  of an XMI root were decoded as strings instead of making use of the
  ``from_string(...)`` method from the type of each attribute. This case is not
  very common, but could still occur.


0.7.12
++++++

**Features**

- Add option for specific XMI "type" field serialization. XMI uses a special
  field to encode the type of the element. This field is almost always named:
  ``xsi:type``, but in some cases, ``xmi:type`` is used instead. To deal with such
  cases, an option is now available: ``XMIOptions.OPTION_USE_XMI_TYPE``.

**Bugfixes**
-  Add missing 'type' field for XMI href serialization. The 'xsi:type' field is
   required when a crossreference is serialized. This field is used to check if
   the resolved resource has the right type (not really, but it help). This
   field is kinda optional at the moment for PyEcore, but required for Java-EMF,
   otherwise the EMF will not be able to create the right proxy for the
   crossreferenced resource.


0.7.8/0.7.11
++++++++++++

**Features**

- Add missing ``eAllAttributes()`` method for retriving all
  ``eStructuralFeatures`` that are ``EAttributes``.

**Bugfixes**

- Fix issue with double notification for x..1--x..* opposite references. When a
  relationship with an eOpposite involving a x..1 and a x..* relationship, in
  case the x..1 was set, the x..* opposite update was doing a "double set",
  thus throwing two times the notification.


0.7.7
+++++

**Bugfixes**

- Improve ``EClass`` dynamic modifications. The ``__init__`` method of the
  ``EClass`` was responsible for the registration of an 'eternal_listener'
  (a listener that cannot be removed. In case the ``EClass`` instance was
  created using ``__new__`` then using ``__init__`` to set some values in the
  parameter, the listener was registered **after** the set of some values.
  This implies that some modifications (name modification for example)
  couldn't be took into account in the method that sync the python class with
  the ``EClass`` instance.


0.7.6
+++++

**Features**

- Add options support for JSON serialization. Currently, the only JSON
  serialization option that is added is: ``SERIALIZE_DEFAULT_VALUE``. This
  option allows the user to serialize feature values that are equal to the
  default ones.


**Bugfixes**

- Fix bad default value for ``xxxObject`` data types. These data types (e.g:
  ``EIntegerObject``) must have a ``None`` default value as they do not represent
  the Java boxed type, but their **object** version. This fix introduces a real
  difference between boxed types and non-boxed types.


0.7.5
+++++

**Features**

- Add easier way of dynamically add behavior to ``EClass``. This features adds
  the ability to register function to existing dynamic and static ``EClass``.

**Bugfixes**

- Fix missing exception when affecting single element to collection. When a
  single assignement is done on a collection-kind meta-attribute, an exception
  must be raised as the 'attribute' type is, somehow, modified.

**Miscellaneous**

- Improve the ``eResource`` management. This reduces memory footprint, slightly
  improves big model serialization, and avoides 'unsync' objects with their
  resource.

0.7.4
+++++

**Features**

- Add dedicated method for eclass ref serialization in ``JsonResource``. This
  method allows the user to override it if required in order to control a little
  bit the way the JSON will be produced. If the users override this method by
  providing a new implementation, they also should override the eclass resolve
  method. Otherwise, the deserialization of a previously serialized model with
  this new implementation will fail. The two methods to override are the
  following:

  - ``serialize_eclass(self, eclass)``
  - ``resolve_eclass(self, uri_eclass)``

  Note that for the ``resolve_eclass`` method, the use of a cache like
  ``lru_cache`` is often a good idea.

- Remove systematic serialization of ``EClass`` reference in JSON serializer. In
  some cases where the containing feature type is the same than the serialized
  object, the ``eClass`` entry in the JSON resource is not required. This allows
  to reduce the resource size a little bit more.

- Change the ``EEnum`` implementation for default values. The default value of
  an ``EENum`` is computed from the first element in the ``eLiterals``. The
  change of a ``default_value`` is performed by 'reordering' the ``eLiterals``
  list.


**Bugfixes**

- Refactor ``EProxy`` implementation. The new ``EProxy`` implementation get rid
  of the ``EPlaceHolder`` class that was used for bad reasons. Now, an
  ``EProxy`` inherits from an ``EObject``. As a side-effect, this also fixes an
  issue in the JSON serialization: ``EProxy`` were not resolved, and,
  consequently, a ``Resource`` with ``EProxy`` inside was not serializable.

- Remove Ecore metamodel from a Resource. Each metamodel registered in a
  ``ResourceSet`` or the ``global_registry`` should not be part of a
  ``Resource``. The fact that they are registered in a ``Resource`` implies that
  they are part of the same level than the ``Resource`` which is serialized.
  However, they are part of something "greater".

- Add special deserialization method for ``EEnum``. The basic deserialization
  method for ``EEnum`` instance was the same than the one for ``EDataType``.
  They only takes the string and put it in the feature instance. Instead, when
  a string is found for an ``EEnum`` feature, the ``EEnumLiteral`` must be
  searched. This new ``from_string`` implementation just does this.


0.7.3
+++++

**Features**

- Performance improvement for JSON deserialization. The use of the ``lru_cache``
  enables the JSON resource to quickly identify metaclasses once they are
  resolved.

**Bugfixes**

- Fix issue with JSON serializer when multiples subpackages are used. The
  ``eClass`` relationship, serialized in the form of the root ``EPackage`` uri
  with the ``EClass`` uri fragment were badly formed.

- Fix calls in ``XMIResource`` and ``JsonResource`` for ``URI`` handling. This
  new way of calling an ``URI`` input/output stream creation enables a simpler
  creation of new dedicated ``URI``. As example, a ``StringURI`` is added in
  the ``README.rst``.


0.7.2
+++++

**Miscellaneous**

- Change the usage of ``MutableSequence`` for ``UserList`` instead, reducing
  some boilerplate code.
- Add missing ``@staticmethod`` when required.


0.7.0/0.7.1
+++++++++++

**Features**

- Add ``XMLTypes`` implementation. This first implementation relies on
  ``XMLTypes.ecore`` and had been generated using pyecoregen. The generated code
  had been manually modified to deal with some current restriction in PyEcore.
  The result is a slightly modified version of some ``EClass`` defined in the
  xml types metamodel. These modifications does not affect the model layer which
  will work as intended, but can give some false information about some types
  when reflection on the xml types metamodel is used.

- Add very basic EMF Editing Domain implementation. This simple implementation
  allows the user to create/load a resource and to execute/undo/redo commands
  that implies element from a resource contained in the Editing domain's
  ``ResourceSet``. This implementation will evolve by probably adding read only
  resource support and copy/paste functionnality.

- Add basic support for ``OrderedSet``'s' ``__setitem__`` method. This very
  simple implementation relies on ``insert`` and ``pop`` and currently does
  not support ``slices``.

- Add ``__iadd__`` support for collections. This little addition allows you to
  add elements to PyEcore collections using ``+=``. This operator also works
  for single element as right operand.

- Add ``del obj.attr`` support for ``EObject`` attributes/references. The
  support for the ``del`` keywords is only activated on ``EStructuralFeature``
  instances. It allows to clean references on elements for a given object.
  **WARNING:** this action does not delete the pointed object, it only clears
  the reference/collection from the calling element towards the objects.

- Add support for ``dir`` on ``EObject``. The function ``dir()`` now gives a
  sum up of all the attributes/references and operations that can be called on
  an object. This is really handy when PyEcore is handled in the Python console.

- Add ``**kwargs`` support for dynamic ``EClass``. This allows to have more
  fluent constructors. It is important to note that the default behavior when
  a named parameter are used is to set the attribute to the value passed as
  parameter. Also, ``args`` are accepted, but they are not directly handled.

- Add new class decorator for PyEcore metaclass definition. This new decorator:
  ``@EMetaclass``, uses the ``MetaEClass`` metaclass and provides a convenient
  way of defining static EClass. This decorator also reoder the inheritance
  tree so, if the defined class does not inherits from ``EObject``, the
  decorator makes the defined class inhertit from ``EObject``.

-  Add JSON resource serializer. The JSON serializer is able to get an
   ``EObject`` and serialize it in JSON. It can also takes a JSON representation
   of a model, and transform it as an ``EObject``. The JSON format used for
   serialization tries to be closed to the format from the
   `emfjson-jackson <https://github.com/emfjson/emfjson-jackson>`_ project.


**Bugfixes**

- Fix missing ``EDatatypes`` registration in their respective ``EPackage``. The
  data types defined in code generated by pyecoregen was not properly registered
  in their ``EPackage``. The result was a ``None`` value when
  ``datatype.ePackage`` was accessed.

- Fix resource creation if model loading fails for ``ResourceSet``. Even if the
  model loading fails, a resource is created in a ResourceSet. This behavior
  was problematic as two successive loading of the same faulty model lead to a
  failure the first time, but to a success the next time. This commit fixes
  this behavior and adds more tests to detect possible regressions about this.

- Fix load error when metamodel prefix is empty. When a metamodel prefix is
  empty, special tags, with the namespace encoded inside, are created by lxml.
  This was an issue with the xmi loading method as each tag's node was not
  properly decoded.

- Improve OrderedSet ``insert/pop`` methods. The default ``OrderedSet``
  implementation does not provide methods for ``insert`` and ``pop``. The
  current code provided by PyEcore, monkey patching the library, was mixed
  with internal PyEcore code. This new implementation split the two concerns
  and proposes a better way of dealing with these two methods.

- Fix missing ``containement`` attribute for ``eParameters`` relation. This
  missing attribute was reslting in the placement of each ``EParameter`` at
  the root of the model instead of the ``EOperation`` they were linked to.

**Miscellaneous**

- Change ``__repr__`` display for ``EClass`` and ``EStructuralFeature``. The
  fact that PyEcore is extensible and the basic ``EClass/EStructural``
  metaclasses can  be extended requires a better representation.

- Add ``__name__`` attribute on instances of ``EClass`` so they look a little
  bit more like a python class.

- Improve inheritance tree building for static ``EClass``. This new detection
  relies on the fact that an existing EClass already have an ``eClass``
  attribute. This modification will prepare the work for the introduction of a
  new method for generating static ``EClass``.

- Add missing ``super().__init__()`` call in base classes. This missing
  statement could be an issue for multiple inheritance.

- Add better support for ``**kwargs`` in ``EObject`` constructors.

- Improve performance. As attribute are accessed in a lazy-loading way, there
  is no more need for post object creation initialization.


0.6.0
+++++

**Features**

- Add multiplicity parameter for ``EParameter/EOperation`` constructors.
  Parameter and Operations can express a multiplicity like ``1..*`` if wanted.
  This attribute can be modified after one of these object had been created,
  but it wasn't possible to give the multiplicity during the object creation.
  This commit simply add the missing parameters in the constructors.

- Add new way of dealing with ``isinstance``. The ``isinstance`` method from
  the ``EcoreUtils`` class was not very effective and was gathering all cases
  in a big ``if/elif/else`` block. This commit defers all the ``isinstance``
  to a method ``__isinstance__``, implemented in each required elements. This
  commit also introduce a new way of init for each ``EStructuralFeature``
  attributes when an instance is created.

**Bugfixes**

- Fix intra-document references by proxy. A reference between elements can also
  be done using a 'full' URI, i.e: specifying the uri/path of the resource to
  access and the path towards the object. This way of referencing elements is
  not reserved to metamodel references, but can be done with any kind of
  references. To deal with this, a proxy is introduced each time such a
  reference is done. This allows to relies on the same mechanism as the href
  one and gives a better control over their resolutions.

- Fix ``ResourceSet`` local resource resolving. When a local resource is searched,
  the path and its uri is split. Once the uri is split, its path is searched in
  the 'resources' of the ``ResourceSet``. This search was done in a 'file' like only
  researched, while the uri could be a logical one (for the ``plateform:/``
  like uri).

- Fix missing ``name`` feature validation. The name feature was only handled as
  a simple python attribute instead of an EAttribute. This time, the ``name``
  feature is handled as an ``EAttribute``. As each instance of ``EAttribute``
  needs to use its own name (which is an ``EAttribute``), it is required to cut
  the recursive call. To do so, the ``EStructuralFeature`` listen to each
  changes performed on itself. If a modification occurs on the ``name`` feature,
  it keeps a simple python attribute version which can be used in the
  ``EStructuralFeature`` descriptor.


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
