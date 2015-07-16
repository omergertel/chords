import pytest, waiting
from chords.task import requires, Task
from chords.chord import Chord

@pytest.mark.parametrize('exclusive', [True, False])
def test_decorator(initiated_registry, exclusive):
    has_run = []
    
    @requires(int, exclusive, max_value=1)
    def run(resources):
        has_run.append(True)
        assert resources.is_satisfied()
        assert resources.get(int).get_value()==1
        
    run()
    assert has_run

@pytest.mark.parametrize('exclusive', [True, False])
def test_decorator_multiple_resources(initiated_registry, exclusive):
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
def test_decorator_multiple_types(initiated_registry, exclusive):
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
def test_decorator_sleeps_until_free(initiated_registry, exclusive):
    other = Chord()
    other.request(int, True, max_value=2)
    other.acquire()
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

    assert has_run
    assert not other.is_satisfied()

def test_task_with_no_params(initiated_registry):
    has_run = []

    @requires(int, True, max_value=1)
    def run():
        has_run.append(True)

    run()
    assert has_run

def test_subtask(initiated_registry):
    has_run = []

    class TestTask(Task):
        def require(self, resources):
            resources.request(int, True, max_value=1)

        def run(self, resources, *args, **kwargs):
            has_run.append(True)
            assert resources.get(int).get_value() == 1
            secondary = self.step1()
            assert not secondary.is_satisfied()
            self.step2()
            self.step3(resources)

        @requires(int, False, max_value=2)
        def step1(self, resources):
            assert resources.get(int).get_value() == 2
            has_run.append(True)
            return resources

        @requires(int, False, max_value=2)
        def step2(self):
            has_run.append(True)

        @requires(int, False, max_value=2)
        def step3(self, resources, cls_resources):
            # Note how the arguments given to the call have been shifted
            assert cls_resources.get(int).get_value() == 1
            assert resources.get(int).get_value() == 2
            has_run.append(True)

    TestTask().start()
    assert len(has_run) == 4
