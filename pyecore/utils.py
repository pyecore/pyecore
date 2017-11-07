"""
This module gathers utility classes and functions that can ease metamodel and
model manipulation.
"""
from .ecore import EPackage, BadValueError
from .notification import EObserver, Kind


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
