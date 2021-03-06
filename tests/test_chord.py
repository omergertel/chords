import pytest, waiting
from chords.chord import Chord
from chords.fairness_policies import _fairness
from chords.exceptions import UnsatisfiedResourcesError

@pytest.fixture
def chord(request, initiated_registry):
    @request.addfinalizer
    def ensure_cleared():
        assert len(_fairness._queue) == 0
    return Chord()

def test_request(chord):
    chord.request(int, False)
    assert len(chord._requests)==1
    
@pytest.mark.parametrize('exclusive', [True, False])
def test_acquire(chord, exclusive):
    chord.request(int, exclusive)
    assert chord.acquire()
    assert chord.is_satisfied()
    val = chord.get(int).get_value()
    assert 0 <= val and val < 100

@pytest.mark.parametrize('exclusive', [True, False])
def test_acquire_multiple(chord, exclusive):
    chord.request(int, exclusive, max_value=2)
    chord.request(int, exclusive, max_value=2)
    assert chord.acquire()
    assert chord.is_satisfied()
    vals = [r.get_value() for r in chord.find(int)]
    assert len(vals) == 2
    assert vals[0] != vals[1]
    for val in vals:
        assert 1 <= val and val <= 2

@pytest.mark.parametrize('exclusive', [True, False])
def test_acquire_multiple_with_get(chord, exclusive):
    chord.request(int, exclusive, max_value=2)
    chord.request(int, exclusive, max_value=2)
    assert chord.acquire()
    assert chord.is_satisfied()
    assert chord.get(int, max_value=1).get_value() == 1
    assert chord.get(int, min_value=2).get_value() == 2

@pytest.mark.parametrize('exclusive', [True, False])
def test_acquire_multiple_with_get_too_many_value(chord, exclusive):
    chord.request(int, exclusive, max_value=2)
    chord.request(int, exclusive, max_value=2)
    assert chord.acquire()
    assert chord.is_satisfied()
    with pytest.raises(UnsatisfiedResourcesError):
        chord.get(int)

@pytest.mark.parametrize('exclusive', [True, False])
def test_acquire_multiple_types(chord, exclusive):
    chord.request(int, exclusive, max_value=1)
    chord.request(float, exclusive, max_value=1)
    assert chord.acquire()
    assert chord.is_satisfied()
    vals = [r.get_value() for r in chord.find(int)]
    assert len(vals) == 1
    assert vals[0] == 1
    vals = [r.get_value() for r in chord.find(float)]
    assert len(vals) == 1
    assert vals[0] == 1

@pytest.mark.parametrize('exclusive', [True, False])
def test_acquire_multiple_types_with_get(chord, exclusive):
    chord.request(int, exclusive, max_value=1)
    chord.request(float, exclusive, max_value=1)
    assert chord.acquire()
    assert chord.is_satisfied()
    assert chord.get(int).get_value() == 1
    assert chord.get(float).get_value()

def test_release(chord):
    chord.request(int, False)
    assert chord.acquire()
    assert chord.is_satisfied()
    chord.release()
    assert not chord.is_satisfied()

@pytest.mark.parametrize('exclusive', [True, False])
def test_acquire_context(chord, exclusive):
    chord.request(int, exclusive, max_value=2)
    chord.request(int, exclusive, max_value=2)
    with chord:
        assert chord.is_satisfied()
        vals = [r.get_value() for r in chord.find(int)]
        assert len(vals) == 2
        assert vals[0] != vals[1]
        for val in vals:
            assert 1 <= val and val <= 2
    assert not chord.is_satisfied()

@pytest.mark.parametrize('exclusive', [True, False])
def test_acquire_context_sleeps_until_free(chord, exclusive):
    other = Chord()
    other.request(int, True, max_value=1)
    other.acquire()
    has_run = []

    orig_wait = waiting.wait
    def wait_and_release(func):
        while not func():
            has_run.append(True)
            other.release()
    waiting.wait = wait_and_release

    try:
        chord.request(int, exclusive, max_value=1)
        chord.request(float, exclusive, max_value=1)
        with chord:
            assert has_run
            assert chord.is_satisfied()
            vals = [r.get_value() for r in chord.find(int)]
            assert len(vals) == 1
            assert vals[0] == 1
    finally:
        waiting.wait = orig_wait
    assert not other.is_satisfied()
    assert not chord.is_satisfied()

def test_acquire_context_sleeps_until_exclusive_free(chord):
    other = Chord()
    other.request(int, False, max_value=1)
    other.acquire()
    has_run = []

    orig_wait = waiting.wait
    def wait_and_release(func):
        while not func():
            has_run.append(True)
            other.release()
    waiting.wait = wait_and_release

    try:
        chord.request(int, True, max_value=1)
        chord.request(float, True, max_value=1)
        with chord:
            assert has_run
            assert chord.is_satisfied()
            vals = [r.get_value() for r in chord.find(int)]
            assert len(vals) == 1
            assert vals[0] == 1
    finally:
        waiting.wait = orig_wait
    assert not other.is_satisfied()
    assert not chord.is_satisfied()

def test_fail_get_if_not_satisfied(chord):
    chord.request(int, False)
    with pytest.raises(UnsatisfiedResourcesError):
        chord.get(int)
    assert chord.acquire()
    chord.release()
    with pytest.raises(UnsatisfiedResourcesError):
        chord.get(int)

def test_fail_find_if_not_satisfied(chord):
    chord.request(int, False)
    with pytest.raises(UnsatisfiedResourcesError):
        chord.find(int)
    assert chord.acquire()
    chord.release()
    with pytest.raises(UnsatisfiedResourcesError):
        chord.find(int)

def test_exception_handling(chord):
    chord.request(int, True, max_value=2)
    chord.request(int, True, max_value=2)
    with pytest.raises(ValueError):
        with chord:
            raise ValueError()
    assert not chord.is_satisfied()

def test_get(chord):
    chord.request(int, True, max_value=2)
    chord.request(int, True, max_value=2)
    with chord:
        assert chord.get(int, max_value=1).get_value() == 1

def test_get_params_different_than_request(chord):
    chord.request(int, True, max_value=2)
    chord.request(int, True, max_value=2)
    with chord:
        assert chord.get(int, min_value=2).get_value() == 2

def test_fail_get_wrong_class(chord):
    chord.request(int, True, max_value=2)
    chord.request(int, True, max_value=2)
    with chord:
        with pytest.raises(UnsatisfiedResourcesError):
            chord.get(float)

def test_fail_get_ambigous_params(chord):
    chord.request(int, True, max_value=2)
    chord.request(int, True, max_value=2)
    with chord:
        with pytest.raises(UnsatisfiedResourcesError):
            chord.get(int)

def test_fail_get_no_matches(chord):
    chord.request(int, True, max_value=2)
    chord.request(int, True, max_value=2)
    with chord:
        with pytest.raises(UnsatisfiedResourcesError):
            chord.get(int, min_value=3)
