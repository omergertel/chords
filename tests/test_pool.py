import pytest
from chords.request import Request
from .conftest import TestResource, TestPool
from chords.exceptions import UnsatisfiableRequestError
        
@pytest.fixture
def pool():
    return TestPool(int)


def test_add(pool):
    length = len(pool.all())
    pool.add(TestResource(int, 101))
    assert length + 1 == len(pool.all())

def test_remove(pool):
    length = len(pool.all())
    pool.remove(TestResource(int, 1))
    assert length - 1 == len(pool.all())

def test_fail_remove_not_exists(pool):
    pool.remove(TestResource(int, 1))
    with pytest.raises(ValueError):
        pool.remove(TestResource(int, 1))

def test_find(pool):
    result = [x.get_value() for x in pool.find(Request(int, min_value=5, max_value=10))]
    assert result == [5, 6, 7, 8, 9, 10]

def test_wrong_request(pool):
    with pytest.raises(UnsatisfiableRequestError):
        pool.get(Request(float))
    with pytest.raises(UnsatisfiableRequestError):
        pool.get(Request(int, min_value=200))

@pytest.mark.parametrize("exclusive", [False, True])
def test_resource_acquired(pool, exclusive):
    req = Request(int, exclusive=exclusive, max_value=1)
    resource = pool.get(req)
    assert resource.get_value() == 1
    resource.acquire(req)
    resource = pool.get(req)
    assert resource is None if exclusive else resource.get_value() == 1 # Shared can be acquired again, but exclusive can't
