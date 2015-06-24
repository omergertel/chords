from .resource import Resource

class Pool(object):
    def __init__(self):
        self._resources = []

    def add(self, resource):
        assert isinstance(resource, Resource)
        self._resources.append(resource)

    def remove(self, resource):
        self._resources.remove(resource)

    def find(self, request):
        for resource in self._resources:
            if resource.can_acquire(request) and resource.matches(request):
                yield resource

    def get(self, request):
        """
        Return the first resource matching the request
        """
        for resource in self.find(request):
            return resource

    def __len__(self):
        return len(self._resources)

class HashPool(Pool):
    def __init__(self, key=None):
        self._resources = {}
        if key is None:
            key = lambda x:x
        self._key = key

    def add(self, resource):
        self._resources[self._key(resource)] = resource

    def remove(self, resource):
        del self._resources[self._key(resource)]

    def find(self, request):
        if 'key' in request.kwargs and request.kwargs.get('key') in self._resources:
            resource = self._resources[request.kwargs.get('key')]
            if resource.can_acquire(request):
                yield resource
        else:
            for resource in self._resources.values():
                if resource.can_acquire(request) and resource.matches(request):
                    yield resource
