import pyecore.ecore as Ecore

def mapping(f):
    RESULT = 'result'
    @functools.wraps(f)
    def inner(*args, **kwargs):
        inparm = tuple(args + tuple(kwargs.values()))
        try:
            return map_result[inparm]
        except KeyError:
            pass
        outEClass = typing.get_type_hints(f)['return']
        if outEClass is Ecore.EClass:
            result = outEClass('tmp_name')
        else:
            result = outEClass()
        map_result[inparm] = result
        g = f.__globals__
        marker = object()
        oldvalue = g.get(RESULT, marker)
        g[RESULT] = result
        try:
            f(*args, **kwargs)
        finally:
            if oldvalue is marker:
                del g[RESULT]
            else:
                g[RESULT] = oldvalue
        print(f'TRACE {f.__name__}[src={inparm}, dest={result}]')  # Python 3.6 only
        return result
    return inner


class when(object):
    def __init__(self, condition):
        self.condition = condition

    def __call__(self, f):
        @functools.wraps(f)
        def inner(*args, **kwargs):
            if self.condition(*args, **kwargs):
                return f(*args, **kwargs)
            else:
                return None
        return inner


class disjunct(object):
    def __init__(self, *args):
        self.list = args

    def __call__(self, f):
        @functools.wraps(f)
        def inner(*args, **kwargs):
            for fun in self.list:
                result = fun(*args, **kwargs)
                if result is not None:
                    break
            f(*args, **kwargs)
            return result
        return inner


class mappingwhen(object):
    def __init__(self, condition):
        self.condition = condition

    def __call__(self, f):
        @functools.wraps(f)
        @when(self.condition)
        @mapping
        def inner(*args, **kwargs):
            return f(*args, **kwargs)
        return inner
