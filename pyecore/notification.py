"""
This module gives the "listener" classes for the PyEcore notification layer.
The main class to create a new listener is "EObserver" which is triggered
each time a modification is perfomed on an observed element.
"""
from enum import unique, Enum


class ENotifer(object):
    def __init__(self, **kwargs):
        super().__init__()

    def notify(self, notification):
        notification.notifier = notification.notifier or self
        for listener in self._eternal_listener + self.listeners:
            listener.notifyChanged(notification)


@unique
class Kind(Enum):
    ADD = 0
    ADD_MANY = 1
    MOVE = 2
    REMOVE = 3
    REMOVE_MANY = 4
    SET = 5
    UNSET = 6


class Notification(object):
    def __init__(self, notifier=None, kind=None, old=None, new=None,
                 feature=None):
        self.notifier = notifier
        self.kind = kind
        self.old = old
        self.new = new
        self.feature = feature

    def __repr__(self):
        return ('[{0}] old={1} new={2} obj={3} #{4}'
                .format(self.kind.name,
                        self.old,
                        self.new,
                        self.notifier,
                        self.feature))


class EObserver(object):
    def __init__(self, notifier=None, notifyChanged=None):
        if notifier:
            notifier.listeners.append(self)
        if notifyChanged:
            self.notifyChanged = notifyChanged

    def observe(self, notifier):
        notifier.listeners.append(self)

    def notifyChanged(self, notification):
        pass
