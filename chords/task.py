import inspect, types
from .pool import HashPool
from .chord import Chord
from .resource import ProxyResource
from . import registry

class Task(object):
    def __init__(self, target=None, name=None):
        """Similar to threads, if target is not None, will run target. You may also override the run method."""
        self._run = target
        self._name = name

    def get_name(self):
        if self._name is not None:
            return self._name
        if self._run:
            return self._run.__name__
        return self.__class__.__name__

    def require(self, resources, *args, **kwargs):
        """
        Place requirements for task. Task won't execute until all resources are acquired
            > resources.request(Resource, exclusive=True, **kwargs)
        """
        pass

    def start(self, *args, **kwargs):
        resources = kwargs.pop('resources', Chord())
        resources.request(Task, False, key=self.get_name())
        self.require(resources, *args, **kwargs)
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


class TaskPool(HashPool):
    def add(self, task_or_str):
        if isinstance(task_or_str, Task):
            task_or_str = task_or_str.get_name()
        self._resources[task_or_str] = ProxyResource(task_or_str)

    def find(self, request):
        if 'key' in request.kwargs and request.kwargs.get('key') not in self._resources:
            self.add(request.kwargs.get('key'))
        return super(TaskPool, self).find(request)


registry.register(Task, TaskPool())

### DECORATORS

_default_task_class = Task

def set_default_task_class(task_class):
    global _default_task_class
    _default_task_class = task_class

def get_default_task_class():
    return _default_task_class


class TaskFactory(object):
    def __init__(self, func):
        self._task_class = None
        self._requirements = []
        self._func = func
        self.__name__ = self._func.__name__
        self.__doc__ = self._func.__doc__
    
    def add_requirement(self, cls, exclusive, **kwargs):
        self._requirements.append(dict(cls=cls, exclusive=exclusive, kwargs=kwargs))
    
    def __call__(self, *args, **kwargs):
        task_class = self._task_class or get_default_task_class()
        task = task_class(self._func, name=self.__name__)
        resources = Chord()
        for requirement in self._requirements:
            resources.request(requirement['cls'], requirement['exclusive'], **requirement['kwargs'])
        return task.start(resources=resources, *args, **kwargs)

    def __get__(self, instance, cls):
        return types.MethodType(self, instance or cls)


def task(name=None, task_class=None):
    if task_class is None:
        task_class = get_default_task_class()
    def wrapper(func):
        if not isinstance(func, TaskFactory):
            func = TaskFactory(func)
        if name:
            func.__name__ = name
        if task_class:
            func._task_class = task_class
        return func
    return wrapper


def requires(cls, exclusive=False, **kwargs):
    def wrapper(func):
        if not isinstance(func, TaskFactory):
            task = TaskFactory(func)
            func = task
        func.add_requirement(cls, exclusive, **kwargs)
        return func
    return wrapper
