import random
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
        for resource in self.all():
            if resource.can_acquire(request) and resource.matches(request):
                yield resource

    def get(self, request):
        """
        Return the first resource matching the request
        """
        for resource in self.find(request):
            return resource

    def __iter__(self):
        return self._resources.__iter__()

    def all(self):
        return list(self)


class HashPool(Pool):
    def __init__(self, key=None):
        """
        Key is a callback to get a key for a given resource
        """
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
            for resource in super(HashPool, self).find(request):
                yield resource

    def __iter__(self):
        return self._resources.itervalues()


class RandomPool(Pool):
    def all(self):
        res = super(RandomPool, self).all()
        random.shuffle(res)
        return res

    def remove(self, resource):
        if resource.is_master():
            super(RandomPool, self).remove(resource)

