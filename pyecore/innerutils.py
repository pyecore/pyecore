# -*- coding: future_fstrings -*-
"""
This module gives decorators, functions and variables that are shared among the
different modules.
"""
from contextlib import contextmanager
from datetime import datetime


@contextmanager
def ignored(*exceptions):
    """Gives a convenient way of ignoring exceptions.

    Obviously took from a Raymond Hettinger tweet
    """
    try:
        yield
    except exceptions:
        pass


# Must be completed
# tuple is '(implem_type, use_type_as_factory, default_value)'
javaTransMap = {
    'int': (int, False, 0),
    'boolean': (bool, False, False),
    'byte': (int, False, 0),
    'short': (int, False, 0),
    'long': (int, False, 0),
    'float': (float, False, 0.0),
    'char': (str, False, ''),
    'double': (float, False, 0.0),
    'byte[]': (bytearray, True, None),
    'java.lang.Integer': (int, False, None),
    'java.lang.String': (str, False, None),
    'java.lang.Character': (str, False, None),
    'java.lang.Boolean': (bool, False, False),
    'java.lang.Short': (int, False, None),
    'java.lang.Long': (int, False, None),
    'java.lang.Float': (float, False, None),
    'java.lang.Double': (float, False, None),
    'java.lang.Class': (type, False, None),
    'java.lang.Byte': (int, False, None),
    'java.lang.Object': (object, False, None),
    'java.util.List': (list, True, None),
    'java.util.Set': (set, True, None),
    'java.util.Map': (dict, True, None),
    'java.util.Map$Entry': (dict, True, None),
    'java.util.Date': (datetime, False, None),
    'org.eclipse.emf.common.util.EList': (list, True, None),
    'org.eclipse.emf.ecore.util.FeatureMap': (dict, True, None),
    'org.eclipse.emf.ecore.util.FeatureMap$Entry': (dict, True, None)
}


def parse_date(str_date):
    try:
        return datetime.fromisoformat(str_date)
    except Exception:
        formats = ('%Y-%m-%dT%H:%M:%S.%f%z',
                   '%Y-%m-%dT%H:%M:%S.%f',
                   '%Y-%m-%dT%H:%M:%S',
                   '%Y-%m-%dT%H:%M',
                   '%Y-%m-%d %H:%M:%S.%f%z',
                   '%Y-%m-%d %H:%M:%S.%f',
                   '%Y-%m-%d %H:%M:%S',
                   '%Y-%m-%d %H:%M',
                   '%Y-%m-%d',)
        for format in formats:
            with ignored(ValueError):
                return datetime.strptime(str_date, format)
        raise ValueError('Date format is unknown')
