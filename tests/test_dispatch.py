import pytest
from pyecore.ecore import *
from pyecore.dispatch import dispatch


def test_dispatch_dynamic_mm():
    A = EClass('A')
    B = EClass('B')

    class SequenceSwitch(object):
        def __init__(self):
            self.sequence = []

        @dispatch
        def do_switch(self, o):
            self.sequence.append('Default')

        @do_switch.register(A)
        def _(self, o):
            self.sequence.append('A')

        @do_switch.register(B)
        def _(self, o):
            self.sequence.append('B')

    switch = SequenceSwitch()
    for x in (A(), B(), A(), A(), B()):
        switch.do_switch(x)

    assert switch.sequence == ['A', 'B', 'A', 'A', 'B']


def test_dispatch_static_mm():
    @EMetaclass
    class A(object):
        pass

    @EMetaclass
    class B(object):
        pass

    @EMetaclass
    class Root(object):
        to_a = EReference(eType=A, upper=-1, containment=True)
        to_b = EReference(eType=B, upper=-1, containment=True)

    class SequenceSwitch(object):
        def __init__(self):
            self.a = 0
            self.b = 0
            self.default = 0

        @dispatch
        def do_switch(self, o):
            self.default += 1

        @do_switch.register(A)
        def _(self, o):
            self.a += 1

        @do_switch.register(B)
        def _(self, o):
            self.b += 1

    r = Root()
    r.to_a.extend([A(), A(), A()])
    r.to_b.extend([B(), B()])
    switch = SequenceSwitch()
    for x in r.eAllContents():
        switch.do_switch(x)

    assert switch.a == 3
    assert switch.b == 2
    assert switch.default == 0


def test_dispatch_inheritance_static():
    @EMetaclass
    class A(object):
        pass

    @EMetaclass
    class B(A):
        pass

    @EMetaclass
    class C(B):
        pass

    class InheritanceSwitch(object):
        def __init__(self):
            self.a = 0
            self.b = 0
            self.default = 0

        @dispatch
        def do_switch(self, o):
            self.default += 1

        @do_switch.register(A)
        def _(self, o):
            self.a += 1

        @do_switch.register(B)
        def _(self, o):
            self.b += 1

    switch = InheritanceSwitch()
    for x in [A(), B(), A(), B(), C(), A()]:
        switch.do_switch(x)

    assert switch.a == 3
    assert switch.b == 3
    assert switch.default == 0


def test_dispatch_inheritance_dynamic():
    A = EClass('A')
    B = EClass('B', superclass=(A,))
    C = EClass('C', superclass=(B,))

    class InheritanceSwitch(object):
        def __init__(self):
            self.a = 0
            self.b = 0
            self.default = 0

        @dispatch
        def do_switch(self, o):
            self.default += 1

        @do_switch.register(A)
        def _(self, o):
            self.a += 1

        @do_switch.register(B)
        def _(self, o):
            self.b += 1

    switch = InheritanceSwitch()
    for x in [A(), B(), A(), B(), C(), A()]:
        switch.do_switch(x)

    assert switch.a == 3
    assert switch.b == 3
    assert switch.default == 0


def test_dispatch_default_static():
    @EMetaclass
    class A(object):
        pass

    @EMetaclass
    class B(A):
        pass

    @EMetaclass
    class C(object):
        pass

    class InheritanceSwitch(object):
        def __init__(self):
            self.a = 0
            self.b = 0
            self.default = 0

        @dispatch
        def do_switch(self, o):
            self.default += 1
            assert o.__class__.__name__ not in ('A', 'B')

        @do_switch.register(A)
        def _(self, o):
            self.a += 1
            assert o.__class__.__name__ == 'A'

        @do_switch.register(B)
        def _(self, o):
            self.b += 1
            assert o.__class__.__name__ == 'B'

    switch = InheritanceSwitch()
    for x in [A(), B(), A(), B(), C(), A()]:
        switch.do_switch(x)

    assert switch.a == 3
    assert switch.b == 2
    assert switch.default == 1


def test_dispatch_default_dynamic():
    A = EClass('A')
    B = EClass('B', superclass=(A,))
    C = EClass('C')

    class InheritanceSwitch(object):
        def __init__(self):
            self.a = 0
            self.b = 0
            self.default = 0

        @dispatch
        def do_switch(self, o):
            self.default += 1
            assert o.__class__.__name__ not in ('A', 'B')

        @do_switch.register(A)
        def _(self, o):
            self.a += 1
            assert o.__class__.__name__ == 'A'

        @do_switch.register(B)
        def _(self, o):
            self.b += 1
            assert o.__class__.__name__ == 'B'

    switch = InheritanceSwitch()
    for x in [A(), B(), A(), B(), C(), A()]:
        switch.do_switch(x)

    assert switch.a == 3
    assert switch.b == 2
    assert switch.default == 1
