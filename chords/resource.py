import logbook
from .exceptions import UnsatisfiedResourcesError

_logger = logbook.Logger(__name__)

class Resource(object):
    def __init__(self, cls):
        self.cls = cls
        self._shared = 0
        self._exclusive = False
        self._requests = []

    def is_exclusive(self):
        return self._exclusive

    def is_shared(self):
        return self._shared > 0

    def can_acquire(self, request):
        if self.is_exclusive():
            return False
        if request.is_exclusive():
            return self._shared == 0
        return True

    def acquire(self, request):
        if self._exclusive:
            raise UnsatisfiedResourcesError("Can't acquire exclusive resource {}".format(self))
        if request is not None and request.is_exclusive():
            if self._shared > 0:
                raise UnsatisfiedResourcesError("Can't acquire resource {} exclusively while shared".format(self))
            self._exclusive = True
        else:
            self._shared += 1
        self._requests.append(request)

    def release(self, request):
        if request.is_exclusive():
            if not self._exclusive:
                raise UnsatisfiedResourcesError("Exclusive resource {} can't be released".format(self))
            self._exclusive = False
        else:
            if self._shared == 0 or self._exclusive:
                raise UnsatisfiedResourcesError("Shared resource {} can't be released".format(self))
            self._shared -= 1
        self._requests.remove(request)
        
    def matches(self, request):
        return self.cls == request.cls

