import flux, logging, sys
from collections import OrderedDict

_logger = logging.getLogger('Chords')

ITERATION_MINIMUM = 1


class BestEffortFairness(object):
    """
    Simple queued policy, that lets older chords a chance to acquire resources first.
    We give all chords a fair chance, ordered by age.
    """
    def __init__(self):
        self._queue = OrderedDict()
        self._in_loop = False
        self._last_run = 0

    def add(self, chord):
        self._queue[chord] = chord

    def remove(self, chord):
        self._queue.pop(chord, None)

    def try_acquire_chords(self):
        should_run = (flux.current_timeline.time() - self._last_run) >= ITERATION_MINIMUM
        if not should_run:
            return
        if self._in_loop:
            return
        self._in_loop = True
        self._last_run = flux.current_timeline.time()
        _logger.debug('Trying to acquire {} chords'.format(len(self._queue)))
        for chord in self: # Give everyone a chance to acquire
            try:
                self._handle_chord(chord)
            except Exception as e:
                _logger.debug('Set exception on {}:{}'.format(chord, e))
                chord.set_error(sys.exc_info())
                self.remove(chord)
        self._in_loop = False

    def __iter__(self):
        return list(self._queue).__iter__()
    
    def _handle_chord(self, chord):
        chord.acquire()


class StrictFIFOFairness(BestEffortFairness):
    """
    Always ensure older chords are acquired before newer ones.
    """
    def __iter__(self):
        for chord in list(self._queue):
            if not self._in_loop:
                break
            yield chord
                
    def _handle_chord(self, chord):
        self._in_loop = chord.acquire()


class ExclusiveResourceBlocksFairness(BestEffortFairness):
    """
    When a resource is requested exclusivly, don't allow any new shared locks on it.
    This fairness policy prevents starvation.
    """

    def try_acquire_chords(self):
        self._blocking = set()
        super(ExclusiveResourceBlocksFairness, self).try_acquire_chords()

    def _handle_chord(self, chord):
        if all(request not in self._blocking for request in chord._requests):
            chord.acquire()
        for request in chord._requests:
            if request.is_exclusive():
                self._blocking.add(request)

_fairness = BestEffortFairness()

def set_fairness_policy(policy):
    global _fairness
    _fairness = policy

def try_acquire_chords():
    _fairness.try_acquire_chords()

def add_chord(chord):
    _fairness.add(chord)

def remove_chord(chord):
    _fairness.remove(chord)

