import pytest
from chords.exceptions import UnknownResourceClassError
from chords.pool import Pool
from chords import registry as chord_reg
from chords.request import Request
from .conftest import DummyPool

@pytest.fixture
def registry(request):
    @request.addfinalizer
    def restore():
        if int in chord_reg._registry:
            del chord_reg._registry[int]
    return chord_reg

def test_register(registry):
    registry.register(int, DummyPool(int))
    assert isinstance(registry.get_pool(int), DummyPool)

def test_register_fails_on_type(registry):
    with pytest.raises(TypeError):
        registry.register(int, 1)

def test_register_fails_on_duplicate(registry):
    registry.register(int)
    with pytest.raises(ValueError):
        registry.register(int)
       
def test_register_default_pool(registry):
    registry.register(int)
    assert isinstance(registry.get_pool(int), Pool)
    
def test_unregister(registry):
    registry.register(int)
    registry.unregister(int)
    with pytest.raises(UnknownResourceClassError):
        registry.get_pool(int)

def test_unregister_twice_fails(registry):
    registry.register(int)
    registry.unregister(int)
    with pytest.raises(UnknownResourceClassError):
        registry.unregister(int)

def test_find_resources(registry):
    registry.register(int, DummyPool(int))
    results = [i.get_value() for i in registry.find_resources(Request(int, False, max_value=5))]
    assert results == [1, 2, 3, 4, 5]

def test_get_resource(registry):
    registry.register(int, DummyPool(int))
    results = registry.get_resource(Request(int, False, max_value=5)).get_value()
    assert results in [1, 2, 3, 4, 5]
