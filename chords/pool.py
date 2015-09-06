import random, bisect
from .resource import Resource
from .exceptions import UnsatisfiableRequestError

class Pool(object):
    def __init__(self):
        super(Pool, self).__init__()
        self._resources = []

    def add(self, resource):
        assert isinstance(resource, Resource)
        self._resources.append(resource)

    def remove(self, resource):
        self._resources.remove(resource)

    def find(self, request):
        found = False
        for resource in self.all():
            if resource.matches(request):
                found = True
                if resource.can_acquire(request):
                    yield resource

        if not found:
            raise UnsatisfiableRequestError("No resources can match request {}".format(request))

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
            key = lambda x: x
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


class WeightedRandomPool(Pool):
    """
    Define request.score_method to create a weighted random score. 
    Uniform random is default.
    Score has to be >=0
    """
    def find(self, request):
        found = False
        resources = self.all()

        scores = self._calc_scores(resources, request)

        while resources:
            resource = self._pop_resource(resources, scores)
            if resource.matches(request):
                found = True
                if resource.can_acquire(request):
                    yield resource

        if not found:
            raise UnsatisfiableRequestError("No resources can match request {}".format(request))

    def _calc_scores(self, resources, request):
        score_method = request.kwargs.pop('score_method', lambda _:1)
        scores = []
        for resource in resources:
            scores.append(max(score_method(resource), 0))
        return scores
    
    def _pop_resource(self, resources, scores):
        cum_scores = self._cumsum(scores)
        score_sum = cum_scores[-1]
        score = random.random() * score_sum
        i = bisect.bisect_left(cum_scores, score)
        resource = resources[i]
        del scores[i]
        del resources[i]
        return resource

    def _cumsum(self, scores):
        res = []
        s = 0
        for score in scores:
            res.append(score + s)
            s = res[-1]
        return res
