import inspect, types
from .chord import Chord


class Task(object):
    def __init__(self, target=None):
        """Similar to threads, if target is not None, will run target. You may also override the run method."""
        self._run = target

    def require(self, resources):
        """
        Place requirements for task. Task won't execute until all resources are allocated
            > resources.request(Volume, SHARED, **kwargs)
        """
        pass

    def start(self, *args, **kwargs):
        resources = kwargs.pop('resources', Chord())
        self.require(resources)
        with resources:
            if self._run is None:
                return self.run(resources, *args, **kwargs)

            argnames = inspect.getargspec(self._run)[0]
            is_method = (argnames and 'self' == argnames[0])
            resource_index = 1 if is_method else 0

            # if resources is first arg, pass it down. We don't do fancy arg matching yet
            add_resources = 'resources' in argnames[resource_index:resource_index + 1]
            if add_resources:
                if is_method:
                    args = (args[0], resources) + args[1:]
                else:
                    args = (resources,) + args[1:]

            return self._run(*args, **kwargs)

    def run(self, resources, *args, **kwargs):
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
        task = self._task_class(self._func)
        resources = Chord()
        for requirement in self._requirements:
            resources.request(requirement['cls'], requirement['exclusive'], **requirement['kwargs'])
        return task.start(resources=resources, *args, **kwargs)

    def __get__(self, instance, cls=None):
        return types.MethodType(self, instance, cls)

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
