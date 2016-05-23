import waiting, itertools, logging, sys
from ._compat import reraise
from .exceptions import UnsatisfiedResourcesError
from .request import Request
from . import fairness_policies as fairness
from . import registry

_logger = logging.getLogger('Chords')

class Chord(object):
    def __init__(self):
        self._requests = []
        self._resources = None
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
        Try acquire directly

        Returns:
            True if successful, False otherwise
        """
        if self.is_satisfied() or self._acquire():
            fairness.remove_chord(self)
            return True
        return False

    def _acquire(self):
        """
        Attempt to acquire all resources requested.
        To prevent deadlocks, this is an all-or-nothing approach: resources are only acquired if all requests can be fulfilled.
        
        Returns:
            True if successful, False otherwise
        """
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
                _logger.debug("Can't acquire {}".format(self))
                return False

        # acquire
        _logger.debug('Acquire {} for {}'.format(resources, self))
        for request, resource in self._items(resources):
            resource.acquire(request)

        self._resources = resources
        return True

    def release(self):
        if self.is_satisfied():
            for request, resource in self._items(self._resources):
                resource.release(request)
            _logger.debug('Release {} from {}'.format(self._resources, self))
        self._resources = None

    def set_error(self, error):
        self._error = error

    def _items(self, resource_map):
        return itertools.chain(*[cls_resources.items() for cls_resources in itertools.chain(resource_map.values())])
    
    def _try_acquire(self):
        if self._error:
            raise reraise(self._error[0], self._error[1], self._error[2])
        if self.is_satisfied():
            return True
        fairness.add_chord(self)
        fairness.try_acquire_chords()
        if self._error:
            raise reraise(self._error[0], self._error[1], self._error[2])
        return self.is_satisfied()

    def __iter__(self):
        for resource in self._resources:
            yield resource

    def __contains__(self, resource):
        if self._resources is None:
            return False
        return resource in self._resources

    def __repr__(self):
        return "<Chord {}>".format(self._requests.__repr__() if self._resources is None else self._resources.__repr__())

    def __enter__(self):
        try:
            waiting.wait(self._try_acquire)
            return self
        except:
            self.__exit__(*sys.exc_info())
            raise

    def __exit__(self, exc_type, exc_value, traceback):
        fairness.remove_chord(self)
        self.release()
