from ..pool import Pool

class EphemeralPool(Pool):
    """
    Sometimes it's useful to create a resource out of thin air, that isn't pinned to a concrete resource.
    This might happen when resources have dependencies that are hard to describe using the request semantics,
    like a counter, a bundle of resources or a slice of a list.
    
    If the ephemeral resource requires another resource, you can override can_acquire, acquire and release to also take other resources.
    """
    def create(self, request):
        raise NotImplementedError()

    def find(self, request):
        yield self.create(request)
