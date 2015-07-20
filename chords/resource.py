from .exceptions import UnsatisfiedResourcesError

class Resource(object):
    def __init__(self, cls):
        self.cls = cls
        self._shared = 0
        self._exclusive = False

    def is_exclusive(self):
        return self._exclusive

    def is_shared(self):
        return self._shared > 0

    def can_acquire(self, request):
        if self.is_exclusive():
            return False
        if request.is_exclusive():
            return self._shared == 0
        return True

    def acquire(self, request):
        if self._exclusive:
            raise UnsatisfiedResourcesError("Can't acquire exclusive resource {}".format(self))
        if request is not None and request.is_exclusive():
            if self._shared > 0:
                raise UnsatisfiedResourcesError("Can't acquire resource {} exclusively while shared".format(self))
            self._exclusive = True
        else:
            self._shared += 1

    def release(self, request):
        if request.is_exclusive():
            if not self._exclusive:
                raise UnsatisfiedResourcesError("Exclusive resource {} can't be released".format(self))
            self._exclusive = False
        else:
            if self._shared == 0 or self._exclusive:
                raise UnsatisfiedResourcesError("Shared resource {} can't be released".format(self))
            self._shared -= 1
        
    def matches(self, request):
        return self.cls == request.cls

class ProxyResource(Resource):
    """
    A thin wrapper around an object that turns it into a resource, but proxies all attributes to the original object
    """
    def __init__(self, obj):
        super(ProxyResource, self).__init__(obj.__class__)
        super(ProxyResource, self).__setattr__("_obj", obj)

    def __getattribute__(self, k):
        try:
            return super(ProxyResource, self).__getattribute__(k)
        except AttributeError:
            return getattr(super(ProxyResource, self).__getattribute__("_obj"), k)

    def __eq__(self, o):
        if isinstance(o, ProxyResource):
            o = o._obj
        return self._obj == o

    def __ne__(self, o):
        return not self == o

    def __hash__(self):
        return self._obj.__hash__()

    def __repr__(self):
        return self._obj.__repr__()

