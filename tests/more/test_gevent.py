import pytest, flux, gevent
from chords.task import set_default_task_class, get_default_task_class, requires
from chords.more.gevent_task import GeventTask

@pytest.fixture(autouse=True)
def timer(request):
    old_timer = flux.current_timeline.get()
    flux.current_timeline.set(flux.GeventTimeline())
    @request.addfinalizer
    def restore():
        flux.current_timeline.set(old_timer)

@pytest.fixture(autouse=True)
def task_class(request):
    old_class = get_default_task_class()
    set_default_task_class(GeventTask)
    @request.addfinalizer
    def restore():
        flux.current_timeline.set(old_class)
    

@pytest.mark.parametrize('exclusive', [True, False])
def test_decorator_sleeps_until_free(initiated_registry, exclusive):
    run_counter = []
    
    @requires(int, exclusive, max_value=2)
    @requires(int, exclusive, max_value=2)
    def task_func(resources):
        run_counter.append(True)
        old_counter = len(run_counter)

        assert resources.is_satisfied()
        flux.current_timeline.sleep(1)
        assert resources.is_satisfied()
        vals = [v.get_value() for v in resources.find(int)]
        assert len(vals) == 2

        if exclusive:
            assert old_counter == len(run_counter), "Other task didn't wait for this to finish"
        else:
            assert old_counter == 2 or old_counter < len(run_counter), "Other task should have started in parallel"
        return old_counter

    res1 = task_func()
    res2 = task_func()
    assert res1.get() == 1
    assert res2.get() == 2
    assert len(run_counter) == 2
