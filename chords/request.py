
class Request(object):
    def __init__(self, cls, exclusive=False, **kwargs):
        self.cls = cls
        self.kwargs = kwargs
        self._exclusive = exclusive

    def is_exclusive(self):
        return self._exclusive

    def is_shared(self):
        return not self._exclusive

    def __getattribute__(self, k):
        try:
            return object.__getattribute__(self, k)
        except AttributeError:
            return self.kwargs.get(k)

    def __repr__(self):
        return "<Request {} {} {}>".format('Exclusive' if self._exclusive else '', self.cls, self.kwargs)

    def __eq__(self, o):
        if not isinstance(o, Request):
            return False
        return self.cls == o.cls and self.kwargs == o.kwargs

    def __ne__(self, o):
        return not self == o

    def __hash__(self):
        return super(Request, self).__hash__()
