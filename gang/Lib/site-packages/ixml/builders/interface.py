class ObjectBuilder(object):  # pragma: no cover

    """
    Provides a uniform API to incrementally build python objects from XML parser events.

    Events are passed into the ``event`` function that accepts three parameters: path, event type and value.
    The object being built is available at any time from the ``value`` attribute.

    """

    def __init__(self, root=None):
        raise NotImplementedError()

    def event(self, path, event, value):
        raise NotImplementedError()
