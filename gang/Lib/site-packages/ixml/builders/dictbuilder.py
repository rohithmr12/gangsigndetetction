from .interface import ObjectBuilder


class DictObjectBuilder(ObjectBuilder):

    """
    Incrementally builds a dict object from XML parser events.

    Example::

    >>> from StringIO import StringIO
    >>> import ixml
    >>> xml = '''<?xml version="1.0" encoding="utf-8"?>
    ...     <rss version="2.0">
    ...         <channel>
    ...             <item xmlns="http://www.defaultns.com">
    ...                 <title>Title item 1</title>
    ...                 <desc>Desc item 1</desc>
    ...                 <category>Cat item 1</category>  <!-- A COMMENT -->
    ...             </item>
    ...             <item xmlns:ns2="http://www.ns2.com">
    ...                 <ns2:title>Title item 2</ns2:title>
    ...                 <ns2:desc>Desc item 2</ns2:desc>
    ...                 <ns2:category>Cat item 2</ns2:category>
    ...             </item>
    ...         </channel>
    ...     </rss>'''
    >>> data = StringIO(xml)
    >>> builder = DictObjectBuilder()    
    >>> for path, event, value in ixml.parse(data):
    ...     builder.event(path, event, value)
    >>> builder.value == {
    ...     'rss': {
    ...         '@version': '2.0',
    ...         'channel': {
    ...             'item': [
    ...                 {
    ...                     'category': 'Cat item 1',
    ...                     'desc': 'Desc item 1',
    ...                     'title': 'Title item 1'
    ...                 },    
    ...                 {
    ...                     'ns2:category': 'Cat item 2',
    ...                     'ns2:desc': 'Desc item 2',
    ...                     'ns2:title': 'Title item 2'
    ...                 }
    ...             ]
    ...         }
    ...     }
    ... }
    True

    """

    def __init__(self, root=None):
        
        self.roots = []
        if root is not None:
            self.roots.append('{}.'.format(root))

        self.value = {}  # The main build object
        self.containers = [self.value]

    def _make_key(self, path):
        if self.roots:
            return path.replace(self.roots[-1], '')  # removes the root
        return path

    def _handle(self, path, value):
        key = self._make_key(path)
        container = self.containers[-1]

        # If it aready exists, we need a list to append the value
        if key in container:
            if isinstance(container[key], list):
                container[key].append(value)
            else:
                container[key] = [container[key], value]
        else:
            container[key] = value

    def event(self, path, event, value):

        if event == 'data':
            self._handle(path, value)

        # Containers: sub elements
        elif event == 'start':
            new_container = {}
            self._handle(path, new_container)

            self.containers.append(new_container)
            self.roots.append('{}.'.format(path))

        elif event == 'end':
            self.containers.pop()
            self.roots.pop()
