import logging
from .pool import Pool
from .exceptions import UnknownResourceClassError

_registry = {}
_logger = logging.getLogger('Chords')

def register(cls, pool=None):
    if cls in _registry:
        raise ValueError('{} is already registered'.format(cls))
    if pool is None:
        pool = Pool()
    if not isinstance(pool, Pool):
        raise TypeError('Expected Pool, got {}'.format(pool))
    _logger.debug('Registering {}'.format(cls))
    _registry[cls] = pool
    return pool

def unregister(cls):
    if not cls in _registry:
        raise UnknownResourceClassError("{} is not registered".format(cls))
    _logger.debug('Ungistering {}'.format(cls))
    del _registry[cls]

def get_pool(cls):
    if not cls in _registry:
        raise UnknownResourceClassError("{} is not registered".format(cls))
    return _registry[cls]

def get_resource(request):
    if not request.cls in _registry:
        raise UnknownResourceClassError("{} is not registered".format(request.cls))
    return _registry[request.cls].get(request)

def find_resources(request):
    if not request.cls in _registry:
        raise UnknownResourceClassError("{} is not registered".format(request.cls))
    return _registry[request.cls].find(request)

