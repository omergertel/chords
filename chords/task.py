from .chord import Chord

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
            self.run(*args, **kwargs)

    def run(self, *args, **kwargs):
        """
        Do stuff
        """
        raise NotImplementedError()


class FunctionTask(Task):
    def __init__(self, func):
        super(FunctionTask, self).__init__()
        self._func = func
        self.__name__ = self._func.__name__
        self.__doc__ = self._func.__doc__
    
    def add_requirement(self, cls, exclusive, **kwargs):
        self._resources.request(cls, exclusive, **kwargs)
    
    def run(self, *args, **kwargs):
        self._func(self._resources, *args, **kwargs)
        
    def __call__(self, *args, **kwargs):
        self.start()


def requires(cls, exclusive=False, **kwargs):
    def wrapper(func):
        if not isinstance(func, FunctionTask):
            func = FunctionTask(func)
        func.add_requirement(cls, exclusive, **kwargs)
        return func
    return wrapper
