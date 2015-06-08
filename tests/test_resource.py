import pytest
from chords.request import Request
from chords.resource import Resource
from chords.exceptions import UnsatisfiedResourcesError

@pytest.fixture(params=[True, False])
def req(request):
    return Request(int, request.param)


@pytest.fixture
def resource():
    return Resource(int)


def test_acquire(req, resource):
    assert resource.can_acquire(req)
    assert resource.matches(req)
    resource.acquire(req)
    assert resource.is_shared() == req.is_shared()
    assert resource.is_exclusive() == req.is_exclusive()

def test_fail_exclusive_already_acquired(req, resource):
    assert resource.can_acquire(req)
    assert resource.matches(req)
    resource.acquire(req)
    with pytest.raises(UnsatisfiedResourcesError):
        exclusive_req = Request(int, True)
        assert not resource.can_acquire(exclusive_req)
        resource.acquire(exclusive_req)
    assert resource.is_shared() == req.is_shared()
    assert resource.is_exclusive() == req.is_exclusive()

def test_fail_acquire_exclusive(req, resource):
    exclusive_req = Request(int, True)
    assert resource.can_acquire(exclusive_req)
    resource.acquire(exclusive_req)
    with pytest.raises(UnsatisfiedResourcesError):
        assert not resource.can_acquire(req)
        resource.acquire(req)
    assert not resource.is_shared()
    assert resource.is_exclusive()

def test_acquire_shared_twice(resource):
    shared_req = Request(int, False)
    assert resource.can_acquire(shared_req)
    resource.acquire(shared_req)
    assert resource.can_acquire(shared_req)
    resource.acquire(shared_req)
    assert resource.is_shared()
    assert resource._shared == 2
    assert not resource.is_exclusive()

def test_release(req, resource):
    resource.acquire(req)
    resource.release(req)
    assert not resource.is_shared()
    assert not resource.is_exclusive()

def test_fail_release_unacquired(req, resource):
    with pytest.raises(UnsatisfiedResourcesError):
        resource.release(req)

def test_fail_release_twice(req, resource):
    resource.acquire(req)
    resource.release(req)
    with pytest.raises(UnsatisfiedResourcesError):
        resource.release(req)

def test_fail_release_exclusive_acquire_shared(resource):
    resource.acquire(Request(int, False))
    with pytest.raises(UnsatisfiedResourcesError):
        resource.release(Request(int, True))

def test_fail_release_shared_acquire_exclusive(resource):
    resource.acquire(Request(int, True))
    with pytest.raises(UnsatisfiedResourcesError):
        resource.release(Request(int, False))

