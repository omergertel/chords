import functools
from gevent import spawn
from ..task import Task

class GeventTask(Task):
    """
    Task that spawns a greenlet
    """
    def start(self, *args, **kwargs):
        return spawn(functools.partial(Task.start, self, *args, **kwargs))
    
