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


def meta_behavior(self, fun):
    setattr(self, fun.__name__, fun)
    return fun


def behavior(self, fun):
    setattr(self.python_class, fun.__name__, fun)
    return fun


ecore.MetaEClass.behavior = meta_behavior
ecore.EClass.behavior = behavior


def main(fun):
    fun.main = True
    return fun


def run(eclass, *args, **kwargs):
    cls = eclass.eClass.python_class
    for _, attr in cls.__dict__.items():
        if inspect.isfunction(attr) and getattr(attr, 'main', False):
            return attr(eclass, *args, **kwargs)
    else:
        raise NotImplementedError('No @main entry point found for {}'
                                  .format(cls))
