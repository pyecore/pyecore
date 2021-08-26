# -*- coding: future_fstrings -*-
"""
This module gathers utility classes and functions that can ease metamodel and
model manipulation.
"""
from .ecore import EPackage, EObject, BadValueError, EClass
from .notification import EObserver, Kind
from functools import singledispatch, update_wrapper
from inspect import ismodule


class DynamicEPackage(EObserver):
    """A DynamicEPackage gives the ability to directly handle metaclasses
    from a metamodel as if it were a statically generated EPackage.

    Usage from an existing dynamic EPackage named 'myroot' that defines two
    EClass: 'A' and 'B'
    >>> from pyecore.utils import DynamicEPackage
    >>> MyAPI = DynamicEPackage(myroot)
    >>> MyAPI.A
    <EClass name="A">
    >>> a = MyAPI.A()
    >>> a
    <pyecore.ecore.A object at 0x7f118de363c8>
    """

    def __init__(self, package):
        if not isinstance(package, EPackage):
            raise BadValueError(got=package, expected=EPackage)
        if ismodule(package):
            package = package.eClass
        super().__init__(notifier=package)

        for eclass in package.eClassifiers:
            setattr(self, eclass.name, eclass)
        for subpackage in package.eSubpackages:
            setattr(self, subpackage.name, DynamicEPackage(subpackage))

    def notifyChanged(self, notification):
        kind = notification.kind
        if notification.feature is EPackage.eClassifiers:
            if kind == Kind.ADD:
                new = notification.new
                setattr(self, new.name, new)
            elif kind == Kind.ADD_MANY:
                for new in notification.new:
                    setattr(self, new.name, new)
            elif kind == Kind.REMOVE and notification.old.eResource is None:
                delattr(self, notification.old.name)
            # elif kind == Kind.REMOVE_MANY:
            #     for element in notification.old:
            #         if element.eResource is None:
            #             delattr(self, element.name)


def dispatch(func):
    dispatcher = singledispatch(func)

    def wrapper(*args, **kw):
        return dispatcher.dispatch(args[1].__class__)(*args, **kw)

    def register(cls, func=None):
        if isinstance(cls, EObject):
            return dispatcher.register(cls.python_class)
        return dispatcher.register(cls)
    wrapper.register = register
    update_wrapper(wrapper, func)
    return wrapper


# def install_issubclass_patch():
#     old_issubclass = builtins.issubclass
#
#     def pyecore_issubclass(self, cls):
#         if isinstance(self, EClass):
#             return old_issubclass(self.python_class, cls)
#         return old_issubclass(self, cls)
#     pyecore_issubclass.original = old_issubclass
#     builtins.issubclass = pyecore_issubclass
#
#
# class original_issubclass(object):
#     def __init__(self):
#         self.pyecore_issubclass = builtins.issubclass
#
#     def __enter__(self):
#         builtins.issubclass = self.pyecore_issubclass.original
#
#     def __exit__(self, type_, value, traceback):
#         builtins.issubclass = self.pyecore_issubclass


def alias(name, feature, eclass=None):
    if eclass is None:
        eclass = feature.eContainingClass
    if isinstance(eclass, EClass):
        setattr(eclass.python_class, name, feature)
    else:
        feature.name = name
        setattr(eclass, name, feature)
