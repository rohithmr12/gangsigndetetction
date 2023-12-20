"""
See README.rst for further information

"""

# Define the API
__all__ = ['parse', 'items']


try:
    # Use LXML: the Pythonic binding for the C libraries libxml2 and libxslt.
    # Known as the fastest XML library in python
    import ixml.backends.lxmliterparse as backend
except ImportError: # pragma: no cover
    # Awaiting a real fallback backend, this makes pip installing works.
    class FakeFallbackBackend(object):
        @staticmethod
        def parse(*args, **kwargs):
            raise Exception(
                'There is currently only a lxml backend so you must install lxml to use it.')
        @staticmethod
        def items(*args, **kwargs):
            raise Exception(
                'There is currently only a lxml backend so you must install lxml to use it.')

    backend = FakeFallbackBackend

    # TODO: direct binding to the C libraries to avoid unused intermediate Element objects?
    # TODO: Fallback to some other backends: standard library ElementTree,
    # etc.?

parse = backend.parse
items = backend.items
