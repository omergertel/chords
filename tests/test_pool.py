import pytest
from chords.request import Request
from .conftest import TestResource, TestPool
from chords.exceptions import UnsatisfiableRequestError
from chords.pool import RandomPool, WeightedRandomPool
        
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


def test_random_pool():
    pool = RandomPool()
    pool._resources = [TestResource(int, i) for i in range(1, 100)]
    result = [x.get_value() for x in pool.find(Request(int, min_value=5, max_value=10))]
    for i in [5, 6, 7, 8, 9, 10]:
        assert i in result

    # There's a tiny tiny chance this might actually be true, if the random shuffle doesn't change the order of these.
    # But what are the odds?
    # Just rerun to make sure it doesn't reproduce.
    assert result != [5, 6, 7, 8, 9, 10]


def test_weighted_random_asc():
    pool = WeightedRandomPool()
    pool._resources = [TestResource(int, i) for i in range(1, 100)]
    largest_number_first = 0
    for _ in range(100):
        result = [x.get_value() for x in pool.find(Request(int, min_value=5, max_value=10, score_method=lambda i:i.get_value() * i.get_value() * i.get_value()))]
        for i in [5, 6, 7, 8, 9, 10]:
            assert i in result
        if result[0] == 10:
            largest_number_first += 1

    assert largest_number_first >= 20 and largest_number_first <= 50


def test_weighted_random_desc():
    pool = WeightedRandomPool()
    pool._resources = [TestResource(int, i) for i in range(1, 100)]
    smallest_number_first = 0
    for _ in range(100):
        result = [x.get_value() for x in pool.find(Request(int, min_value=5, max_value=10, score_method=lambda i:1.0 / i.get_value()))]
        for i in [5, 6, 7, 8, 9, 10]:
            assert i in result
        if result[0] == 5:
            smallest_number_first += 1

    assert smallest_number_first >= 10 and smallest_number_first <= 35
