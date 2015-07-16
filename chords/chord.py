import waiting, itertools, logging, flux, sys
from collections import OrderedDict
from .exceptions import UnsatisfiedResourcesError, ChordError
from .request import Request
from . import registry

_logger = logging.getLogger('Chords')

ITERATION_MINIMUM = 1

class Chord(object):
    _queue = OrderedDict()
    _last_run = 0
    _in_loop = False

    def __init__(self):
        self._requests = []
        self._resources = None
        self._waiting = False
        self._error = None

    def request(self, cls, exclusive=False, **kwargs):
        self._requests.append(Request(cls, exclusive, **kwargs))

    def get(self, cls, **kwargs):
        resources = self.find(cls, **kwargs)
        if len(resources) == 0:
            raise UnsatisfiedResourcesError("Resource {} {} not found in {}".format(cls, kwargs, self))
        if len(resources) > 1:
            raise UnsatisfiedResourcesError("Too many values match {} {} in {}".format(cls, kwargs, self))
        return resources[0]

    def find(self, cls, **kwargs):
        if not self.is_satisfied():
            raise UnsatisfiedResourcesError("Resource context not satisfied")
        if not cls in self._resources:
            raise UnsatisfiedResourcesError("Resource context does not contain resources for {}".format(cls))

        res = []
        request = Request(cls, **kwargs)
        for resource in self._resources[cls].values():
            if resource.matches(request):
                res.append(resource)
        return res

    def is_satisfied(self):
        return self._resources is not None

    def acquire(self):
        """
        Add request to queue, and give a chance for everyone to acquire according to order (for fairness).

        Returns:
            True if successful, False otherwise
        """
        if self.is_satisfied():
            return True # Satisfied before, perhaps by previous iteration on the queue

        force = False
        if self not in Chord._queue: # add to queue
            Chord._queue[self] = self
            force = True
        Chord._try_acquire_chords(force=force)

        if self.is_satisfied(): # Check new status
            return True

        if not self._waiting: # We only reserve place in queue, via context
            Chord._queue.pop(self)
            if self._error:
                raise self._error

        return False

    @classmethod
    def _try_acquire_chords(cls, force=False):
        if cls._in_loop:
            return
        cls._in_loop = True
        try:
            should_run = (flux.current_timeline.time() - cls._last_run) > ITERATION_MINIMUM
            if should_run or force:
                cls._last_run = flux.current_timeline.time()
                _logger.debug('Trying to allocate {} chords'.format(len(Chord._queue)))
                for chord in list(Chord._queue): # Give everyone a chance to acquire
                    _logger.debug('Try allocate {}'.format(chord))
                    if not chord.is_satisfied():
                        if chord._acquire():
                            Chord._queue.pop(chord) # remove if acquired
        finally:
            cls._in_loop = False

    def _acquire(self):
        """
        Attempt to acquire all resources requested.
        To prevent deadlocks, this is an all-or-nothing approach: resources are only acquired if all requests can be fulfilled.
        
        Returns:
            True if successful, False otherwise
        """
        self._error = None

        try:
            resources = {}
            # Get available resources
            for request in self._requests:
                cls_resources = resources.setdefault(request.cls, {})
                found = False
                for resource in registry.find_resources(request):
                    if resource not in cls_resources.values():
                        cls_resources[request] = resource
                        found = True
                        break
                if not found:
                    return False

            # acquire
            for request, resource in self._items(resources):
                _logger.debug('Acquire {} with {}'.format(resource, request))
                resource.acquire(request)

            self._resources = resources
            return True
        except (KeyboardInterrupt, ChordError):
            raise
        except:
            self._error = sys.exc_info()
            _logger.warn('Exception hidden when {} was attempted: {}'.format(self, self._error[0]), exc_info=True)

        return False

    def release(self):
        if self.is_satisfied():
            for request, resource in self._items(self._resources):
                _logger.debug('Release {} from {}'.format(resource, request))
                resource.release(request)
        self._resources = None
        self._waiting = False
        Chord._queue.pop(self, None)

    def _items(self, resource_map):
        return itertools.chain(*[cls_resources.items() for cls_resources in itertools.chain(resource_map.values())])
    
    def __iter__(self):
        for resource in self._resources:
            yield resource

    def __contains__(self, resource):
        if self._resources is None:
            return False
        return resource in self._resources

    def __repr__(self):
        return "<Resources {}>".format(self._requests.__repr__() if self._resources is None else self._resources.__repr__())

    def __enter__(self):
        try:
            self._waiting = True
            waiting.wait(self.acquire)
            return self
        except:
            self.release()
            raise

    def __exit__(self, exc_type, exc_value, traceback):
        self.release()
