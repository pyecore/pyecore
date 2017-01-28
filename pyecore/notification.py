

class ENotifer(object):
    def notify(self, notification):
        notification.notifier = notification.notifier or self
        for listener in self._eternal_listener + self.listeners:
            listener.notifyChanged(notification)


def enum(enumName, *listValueNames):
    """Clever implementation of an enum like in python

    Shameless copy from: http://sametmax.com/faire-des-enums-en-python/
    """
    listValueNumbers = range(len(listValueNames))
    dictAttrib = dict(zip(listValueNames, listValueNumbers))
    dictReverse = dict(zip(listValueNumbers, listValueNames))
    dictAttrib["dictReverse"] = dictReverse
    mainType = type(enumName, (), dictAttrib)
    return mainType


Kind = enum('Kind',
            'ADD',
            'ADD_MANY',
            'MOVE',
            'REMOVE',
            'REMOVE_MANY',
            'SET',
            'UNSET')


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
                .format(Kind.dictReverse[self.kind],
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
