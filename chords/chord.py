import waiting, itertools
from .exceptions import UnsatisfiedResourcesError
from .request import Request
from . import registry

class Chord(object):
    def __init__(self):
        self._requests = []
        self._resources = None

    def request(self, cls, exclusive=False, **kwargs):
        self._requests.append(Request(cls, exclusive, **kwargs))

    def get(self, cls, **kwargs):
        resources = self.find(cls, **kwargs)
        if len(resources) == 0:
            raise UnsatisfiedResourcesError("Resource {} {} not found in {}".format(cls, kwargs, self))
        if len(resources) > 1:
            raise UnsatisfiedResourcesError("Too many values match {} {} in {}".format(cls, kwargs, self))
        return resources[0]

    def find(self, cls, **kwargs):
        if not self.is_satisfied():
            raise UnsatisfiedResourcesError("Resource context not satisfied")
        res = []
        request = Request(cls, **kwargs)
        for _, resource in self._items(self._resources):
            if resource.matches(request):
                res.append(resource)
        return res

    def is_satisfied(self):
        return self._resources is not None

    def allocate(self):
        """
        Attempt to allocate all resources requested.
        To prevent deadlocks, this is an all-or-nothing approach: resources are only allocated if all requests can be fulfilled.
        
        Returns:
            True if successful, False otherwise
        """

        resources = {}
        # Get available resources
        for request in self._requests:
            cls_resources = resources.setdefault(request.cls, {})
            found = False
            for resource in registry.find_resources(request):
                if resource not in cls_resources.values():
                    cls_resources[request] = resource
                    found=True
                    break
            if not found:
                return False

        # acquire
        for request, resource in self._items(resources):
            resource.acquire(request)

        self._resources = resources
        return True

    def release(self):
        if self.is_satisfied():
            if self._resources is not None:
                for request, resource in self._items(self._resources):
                    resource.release(request)
                self._resources = None

    def _items(self, resource_map):
        return itertools.chain(*[cls_resources.items() for cls_resources in itertools.chain(resource_map.values())])
    
    def __iter__(self):
        for resource in self._resources:
            yield resource

    def __contains__(self, resource):
        if self._resources is None:
            return False
        return resource in self._resources

    def __repr__(self):
        return "<Resources {}>".format(self._requests.__repr__() if self._resources is None else self._resources.__repr__())

    def __enter__(self):
        waiting.wait(self.allocate)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.release()
