import pytest, waiting
from chords.task import requires
from chords.chord import Chord
from .conftest import TestPool

@pytest.fixture(autouse=True)
def registry(request, registry):
    registry.register(int, TestPool(int))
    registry.register(float, TestPool(float))
    return registry

@pytest.mark.parametrize('exclusive', [True, False])
def test_decorator(exclusive):
    has_run = []
    
    @requires(int, exclusive, max_value=1)
    def run(resources):
        has_run.append(True)
        assert resources.is_satisfied()
        assert resources.get(int).get_value()==1
        
    run()
    assert has_run

@pytest.mark.parametrize('exclusive', [True, False])
def test_decorator_multiple_resources(exclusive):
    has_run = []

    @requires(int, exclusive, max_value=2)
    @requires(int, exclusive, max_value=2)
    def run(resources):
        has_run.append(True)
        assert resources.is_satisfied()
        vals = [v.get_value() for v in resources.find(int)]
        assert len(vals) == 2
        assert vals[0] != vals[1]
        for v in vals:
            assert 1 <= v <= 2

    run()
    assert has_run

@pytest.mark.parametrize('exclusive', [True, False])
def test_decorator_multiple_types(exclusive):
    has_run = []

    @requires(int, exclusive, max_value=1)
    @requires(float, exclusive, max_value=1)
    def run(resources):
        has_run.append(True)
        assert resources.is_satisfied()
        assert resources.get(int).get_value() == 1
        assert resources.get(float).get_value() == 1

    run()
    assert has_run

@pytest.mark.parametrize('exclusive', [True, False])
def test_decorator_sleeps_until_free(exclusive):
    other = Chord()
    other.request(int, True, max_value=2)
    other.allocate()
    has_run = []
    orig_wait = waiting.wait
    def wait_and_release(func):
        while not func():
            has_run.append(True)
            other.release()
    waiting.wait = wait_and_release

    try:
        @requires(int, exclusive, max_value=2)
        @requires(int, exclusive, max_value=2)
        def run(resources):
            assert has_run
            assert resources.is_satisfied()
            vals = [v.get_value() for v in resources.find(int)]
            assert len(vals) == 2

        run()
    finally:
        waiting.wait = orig_wait
    assert not other.is_satisfied()

