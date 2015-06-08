import pytest
from chords.exceptions import UnknownResourceError
from chords.pool import Pool
from chords.request import Request
from .conftest import TestPool

def test_register(registry):
    registry.register(int, TestPool(int))
    assert isinstance(registry.get_pool(int), TestPool)

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
    with pytest.raises(UnknownResourceError):
        registry.get_pool(int)

def test_unregister_twice_fails(registry):
    registry.register(int)
    registry.unregister(int)
    with pytest.raises(UnknownResourceError):
        registry.unregister(int)

def test_find_resources(registry):
    registry.register(int, TestPool(int))
    results = [i.get_value() for i in registry.find_resources(Request(int, False, max_value=5))]
    assert results == range(1, 6)

def test_get_resource(registry):
    registry.register(int, TestPool(int))
    results = registry.get_resource(Request(int, False, max_value=5)).get_value()
    assert results in range(1, 6)
