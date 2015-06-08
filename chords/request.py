
class Request(object):
    def __init__(self, cls, exclusive=False, **kwargs):
        self.cls = cls
        self.kwargs = kwargs
        self._exclusive = exclusive

    def is_exclusive(self):
        return self._exclusive

    def is_shared(self):
        return not self._exclusive

    def __repr__(self):
        return "<Request {} {} {}>".format('Exclusive' if self._exclusive else '', self.cls, self.kwargs)
