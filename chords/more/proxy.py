from ..resource import Resource

class ProxyResource(Resource):
    """
    A thin wrapper around an object that turns it into a resource, but proxies all attributes to the original object
    """
    def __init__(self, obj):
        super(ProxyResource, self).__init__(obj.__class__.__name__)
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
