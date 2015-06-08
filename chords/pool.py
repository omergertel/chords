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
