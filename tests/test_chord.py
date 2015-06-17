import pytest, waiting
from chords.chord import Chord
from chords.exceptions import UnsatisfiedResourcesError

@pytest.fixture
def chord(initiated_registry):
    return Chord()


def test_request(chord):
    chord.request(int, False)
    assert len(chord._requests)==1
    
@pytest.mark.parametrize('exclusive', [True, False])
def test_allocate(chord, exclusive):
    chord.request(int, exclusive)
    assert chord.allocate()
    assert chord.is_satisfied()
    val = chord.get(int).get_value()
    assert 0 <= val and val < 100

@pytest.mark.parametrize('exclusive', [True, False])
def test_allocate_multiple(chord, exclusive):
    chord.request(int, exclusive, max_value=2)
    chord.request(int, exclusive, max_value=2)
    assert chord.allocate()
    assert chord.is_satisfied()
    vals = [r.get_value() for r in chord.find(int)]
    assert len(vals) == 2
    assert vals[0] != vals[1]
    for val in vals:
        assert 1 <= val and val <= 2

@pytest.mark.parametrize('exclusive', [True, False])
def test_allocate_multiple_with_get(chord, exclusive):
    chord.request(int, exclusive, max_value=2)
    chord.request(int, exclusive, max_value=2)
    assert chord.allocate()
    assert chord.is_satisfied()
    assert chord.get(int, max_value=1).get_value() == 1
    assert chord.get(int, min_value=2).get_value() == 2

@pytest.mark.parametrize('exclusive', [True, False])
def test_allocate_multiple_with_get_too_many_value(chord, exclusive):
    chord.request(int, exclusive, max_value=2)
    chord.request(int, exclusive, max_value=2)
    assert chord.allocate()
    assert chord.is_satisfied()
    with pytest.raises(UnsatisfiedResourcesError):
        chord.get(int)

@pytest.mark.parametrize('exclusive', [True, False])
def test_allocate_multiple_types(chord, exclusive):
    chord.request(int, exclusive, max_value=1)
    chord.request(float, exclusive, max_value=1)
    assert chord.allocate()
    assert chord.is_satisfied()
    vals = [r.get_value() for r in chord.find(int)]
    assert len(vals) == 1
    assert vals[0] == 1
    vals = [r.get_value() for r in chord.find(float)]
    assert len(vals) == 1
    assert vals[0] == 1

@pytest.mark.parametrize('exclusive', [True, False])
def test_allocate_multiple_types_with_get(chord, exclusive):
    chord.request(int, exclusive, max_value=1)
    chord.request(float, exclusive, max_value=1)
    assert chord.allocate()
    assert chord.is_satisfied()
    assert chord.get(int).get_value() == 1
    assert chord.get(float).get_value()

def test_release(chord):
    chord.request(int, False)
    assert chord.allocate()
    assert chord.is_satisfied()
    chord.release()
    assert not chord.is_satisfied()


@pytest.mark.parametrize('exclusive', [True, False])
def test_allocate_context(chord, exclusive):
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
def test_allocate_context_sleeps_until_free(chord, exclusive):
    other = Chord()
    other.request(int, True, max_value=1)
    other.allocate()
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

def test_fail_get_if_not_satisfied(chord):
    chord.request(int, False)
    with pytest.raises(UnsatisfiedResourcesError):
        chord.get(int)
    assert chord.allocate()
    chord.release()
    with pytest.raises(UnsatisfiedResourcesError):
        chord.get(int)

def test_fail_find_if_not_satisfied(chord):
    chord.request(int, False)
    with pytest.raises(UnsatisfiedResourcesError):
        chord.find(int)
    assert chord.allocate()
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
