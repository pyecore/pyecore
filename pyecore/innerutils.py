"""
This module gives decorators and functions that are shared among the different
modules.
"""
from contextlib import contextmanager


@contextmanager
def ignored(*exceptions):
    """Gives a convenient way of ignoring exceptions.

    Obviously took from a Raymond Hettinger tweet
    """
    try:
        yield
    except exceptions:
        pass
