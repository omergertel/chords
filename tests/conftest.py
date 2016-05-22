import sys, pytest
from chords import registry
from chords.pool import Pool
from chords.resource import Resource

class DummyResource(Resource):
    def __init__(self, cls, val):
        Resource.__init__(self, cls)
        self._value = val

    def get_value(self):
        return self._value

    def matches(self, request):
        return (Resource.matches(self, request) and
                self._value <= request.kwargs.get('max_value', sys.maxsize) and
                self._value >= request.kwargs.get('min_value', -sys.maxsize))

    def __eq__(self, o):
        if isinstance(o, DummyResource):
            return self._value == o._value
        return False

    def __ne__(self, o):
        return not self == o

    def __repr__(self, *args, **kwargs):
        return '<Resource {}:{}>'.format(self.cls, self._value)


class DummyPool(Pool):
    def __init__(self, cls):
        Pool.__init__(self)
        self._resources = [DummyResource(cls, i) for i in range(1, 100)]

@pytest.fixture
def initiated_registry(request):
    registry.register(int, DummyPool(int))
    registry.register(float, DummyPool(float))
    @request.addfinalizer
    def restore():
        del registry._registry[int]
        del registry._registry[float]
    return registry
