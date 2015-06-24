import sys, pytest
from chords import registry
from chords.pool import Pool
from chords.resource import Resource

class TestResource(Resource):
    def __init__(self, cls, val):
        Resource.__init__(self, cls)
        self._value = val

    def get_value(self):
        return self._value

    def matches(self, request):
        return (Resource.matches(self, request) and
                self._value <= request.kwargs.get('max_value', sys.maxint) and
                self._value >= request.kwargs.get('min_value', -sys.maxint))

    def __eq__(self, o):
        if isinstance(o, TestResource):
            return self._value == o._value
        return False

    def __ne__(self, o):
        return not self == o

    def __repr__(self, *args, **kwargs):
        return '<Resource {}:{}>'.format(self.cls, self._value)


class TestPool(Pool):
    def __init__(self, cls):
        Pool.__init__(self)
        self._resources = [TestResource(cls, i) for i in range(1, 100)]

@pytest.fixture
def initiated_registry(request):
    registry.register(int, TestPool(int))
    registry.register(float, TestPool(float))
    @request.addfinalizer
    def restore():
        del registry._registry[int]
        del registry._registry[float]
    return registry
