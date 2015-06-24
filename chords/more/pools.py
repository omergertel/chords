import functools, random
from ..pool import Pool

class ScoredPool(Pool):
    def find(self, request):
        resources = [resource for resource in super(ScoredPool, self).find()]
        resources = sorted(resources, functools.partial(self.score, request=request))
        return resources

    def score(self, resource, request):
        """
        Override to allow scoring of resources for this request.
        This can be used to shuffle or give priority to resources that are better fit for this request.
        """
        return 0


class RandomPool(ScoredPool):
    def score(self, resource, request):
        return random.random()
