from .exceptions import UnsatisfiedResourcesError

class Resource(object):
    def __init__(self, cls):
        self.cls = cls
        self._requests = []
        self._exclusive = False

    def is_exclusive(self):
        return self._exclusive

    def is_shared(self):
        return len(self._requests) > 0 and not self.is_exclusive()

    def can_acquire(self, request):
        if self.is_exclusive():
            return False
        if request.is_exclusive():
            return len(self._requests) == 0
        return True

    def acquire(self, request):
        if self.is_exclusive():
            raise UnsatisfiedResourcesError("Can't acquire exclusive resource {}".format(self))
        if request is not None and request.is_exclusive():
            if self.is_shared():
                raise UnsatisfiedResourcesError("Can't acquire resource {} exclusively while shared".format(self))
            self._exclusive = True
        self._requests.append(request)

    def release(self, request):
        if request.is_exclusive():
            if not self.is_exclusive():
                raise UnsatisfiedResourcesError("Non exclusive resource {} can't be released from {}".format(self, request))
            self._exclusive = False
        else:
            if not self.is_shared():
                raise UnsatisfiedResourcesError("Non shared Resource {} can't be released from {}".format(self, request))
        self._requests.remove(request)
        
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

