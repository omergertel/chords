class ChordError(Exception):
    pass

class UnsatisfiedResourcesError(ChordError):
    pass

class UnknownResourceClassError(ChordError):
    pass

class UnsatisfiableRequestError(ChordError):
    pass
