import typing
import pyecore.ecore as Ecore
from functools import lru_cache, wraps
from pyecore.notification import EObserver


class ResultObserver(EObserver):
    def notifyChanged(self, notif):
        print(notif)


class EObjectProxy(object):
    def __init__(self, instance):
        object.__setattr__(self, 'wrapped', instance)
        object.__setattr__(self, 'wrapped_eClass', instance.eClass)

    def __getattribute__(self, name):
        wrapped = object.__getattribute__(self, 'wrapped')
        eClass = object.__getattribute__(self, 'wrapped_eClass')
        result = getattr(wrapped, name)
        if eClass.findEStructuralFeature(name):
            print('access', name, ':', result, 'for', wrapped)
        return result

    def __setattr__(self, name, value):
        wrapped = object.__getattribute__(self, 'wrapped')
        if isinstance(value, EObjectProxy):
            value = object.__getattribute__(value, 'wrapped')
        return setattr(wrapped, name, value)

    def __str__(self):
        wrapped = object.__getattribute__(self, 'wrapped')
        return wrapped.__str__()


def mapping(f):
    f.__mapping__ = True
    result_var_name = 'result'
    f.self_eclass = typing.get_type_hints(f).get('self')
    if f.self_eclass is None:
        raise ValueError("Missing 'self' parameter for mapping: '{}'"
                         .format(f.__name__))
    f.result_eclass = typing.get_type_hints(f).get('return')

    @wraps(f)
    def inner(*args, **kwargs):
        if f.result_eclass is None:
            index = f.__code__.co_varnames.index('self')
            result = kwargs.get('self', args[index])
        elif f.result_eclass is Ecore.EClass:
            result = f.result_eclass('TMP')
        else:
            result = f.result_eclass()
        inputs = [a for a in args if isinstance(a, Ecore.EObject)]
        print('CREATE', result, 'FROM', inputs, 'BY', f.__name__)
        g = f.__globals__
        marker = object()
        oldvalue = g.get(result_var_name, marker)
        g[result_var_name] = result
        observer = ResultObserver(notifier=result)
        new_args = [EObjectProxy(obj)
                    if isinstance(obj, Ecore.EObject)
                    else obj
                    for obj in args]
        for key, value in kwargs:
            if isinstance(value, Ecore.EObject):
                kwargs[key] = EObjectProxy(obj)
        try:
            f(*new_args, **kwargs)
        finally:
            if oldvalue is marker:
                del g[result_var_name]
            else:
                g[result_var_name] = oldvalue
            result.listeners.remove(observer)
        return result
    return lru_cache()(inner)


class when(object):
    def __init__(self, condition):
        self.condition = condition

    def __call__(self, f):
        @wraps(f)
        def inner(*args, **kwargs):
            if self.condition(*args, **kwargs):
                return f(*args, **kwargs)
        return inner


class disjunct(object):
    def __init__(self, *args):
        self.list = args

    def __call__(self, f):
        @wraps(f)
        def inner(*args, **kwargs):
            for fun in self.list:
                result = fun(*args, **kwargs)
                if result is not None:
                    break
            f(*args, **kwargs)
            return result
        return inner


class mapping_when(object):
    def __init__(self, condition):
        self.condition = condition

    def __call__(self, f):
        @wraps(f)
        @when(self.condition)
        @mapping
        def inner(*args, **kwargs):
            return f(*args, **kwargs)
        return inner
