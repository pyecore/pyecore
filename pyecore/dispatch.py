from .ecore import EObject
from functools import singledispatch, update_wrapper


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
