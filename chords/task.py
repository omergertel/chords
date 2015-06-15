from .chord import Chord
import inspect
import functools


class Task(object):
    def __init__(self):
        self._resources = Chord()
    
    def requires(self, resources):
        """
        Place requirements for task. Task won't execute until all resources are allocated
            > resources.request(Volume, SHARED, **kwargs)
        """
        pass

    def start(self, *args, **kwargs):
        self.requires(self._resources)
        with self._resources:
            return self.run(*args, **kwargs)

    def run(self, *args, **kwargs):
        """
        Do stuff
        """
        raise NotImplementedError()


_default_task_class = Task

def set_default_task_class(task_class):
    global _default_task_class
    _default_task_class = task_class

def get_default_task_class():
    return _default_task_class


class TaskFactory(object):
    def __init__(self, func, task_class):
        self._task_class = task_class
        self._requirements = []
        self._func = func
        self.__name__ = self._func.__name__
        self.__doc__ = self._func.__doc__
    
    def add_requirement(self, cls, exclusive, **kwargs):
        self._requirements.append(dict(cls=cls, exclusive=exclusive, kwargs=kwargs))
    
    def __call__(self, *args, **kwargs):
        task = self._task_class()
        task.run = self._func
        if 'resources' in inspect.getargspec(self._func)[0]:
            task.run = functools.partial(self._func, resources=task._resources)

        for requirement in self._requirements:
            task._resources.request(requirement['cls'], requirement['exclusive'], **requirement['kwargs'])
        return task.start()

def requires(cls, exclusive=False, task_class=None, **kwargs):
    if task_class is None:
        task_class = _default_task_class
    def wrapper(func):
        if not isinstance(func, TaskFactory):
            task = TaskFactory(func, task_class)
            func = task
        func.add_requirement(cls, exclusive, **kwargs)
        return func
    return wrapper
