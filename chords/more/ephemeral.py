from ..pool import Pool

class EphemearlPool(Pool):
    """
    Sometimes it's useful to create a resource out of thin air, that isn't stored anywhere
    This often happens when resources have dependencies that are hard to describe using the request semantics,
    but could also help when some condition needs to be met.
    
    A few examples:
     - incrementing a counter
     - taking a slice of a list
    
    """
    def create(self, request):
        raise NotImplementedError()

    def find(self, request):
        while True:
            yield self.create(request)
