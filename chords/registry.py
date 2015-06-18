from .pool import Pool
from .exceptions import UnknownResourceError

_registry = {}

def register(cls, pool=None):
    if cls in _registry:
        raise ValueError('{} is already registered'.format(cls))
    if pool is None:
        pool = Pool()
    if not isinstance(pool, Pool):
        raise TypeError('Expected Pool, got {}'.format(pool))
    _registry[cls] = pool
    return pool

def unregister(cls):
    if not cls in _registry:
        raise UnknownResourceError("{} is not registered".format(cls))
    del _registry[cls]

def get_pool(cls):
    if not cls in _registry:
        raise UnknownResourceError("{} is not registered".format(cls))
    return _registry[cls]

def get_resource(request):
    if not request.cls in _registry:
        raise UnknownResourceError("{} is not registered".format(request.cls))
    return _registry[request.cls].get(request)

def clear():
    _registry.clear()

def find_resources(request):
    if not request.cls in _registry:
        raise UnknownResourceError("{} is not registered".format(request.cls))
    return _registry[request.cls].find(request)
