# -*- coding: future_fstrings -*-
"""The exec module provides new annotations that helps to extend existing
metamodels with behavior, and enables a full executable model experience
in Python.

The added annotations must be use for registering a new function as
metaclass method implementation. Here is an example for static metamodels:

.. code-block:: python
    import my_generated_metamodel as meta

    @meta.MyClass.behavior
    def my_new_fun(self):
        print('In the new fun')

    instance = meta.MyClass()
    instance.my_new_fun()


The exact same code can be applied with dynamic metamodels:

.. code-block:: python

    MyClass = EClass('MyClass')

    @MyClass.behavior
    def my_new_fun(self):
        print('In the new fun from dynamic EClass')

    instance = MyClass()
    instance.my_new_fun()


This same mechanism can also be used for overriding ``EOperation``.
"""
import inspect
from . import ecore


def _meta_behavior(self, fun):
    setattr(self, fun.__name__, fun)
    return fun


def _behavior(self, fun):
    setattr(self.python_class, fun.__name__, fun)
    return fun


ecore.MetaEClass.behavior = _meta_behavior
ecore.EClass.behavior = _behavior


def behavior(cls):
    def inner_decorator(fun):
        if isinstance(cls, type):
            setattr(cls, fun.__name__, fun)
        else:
            setattr(cls.python_class, fun.__name__, fun)
        return fun
    return inner_decorator


def main(fun):
    fun.main = True
    return fun


def run(eclass, *args, **kwargs):
    cls = eclass.eClass.python_class
    for _, attr in cls.__dict__.items():
        if inspect.isfunction(attr) and getattr(attr, 'main', False):
            return attr(eclass, *args, **kwargs)
    raise NotImplementedError(f'No @main entry point found for {cls}')
