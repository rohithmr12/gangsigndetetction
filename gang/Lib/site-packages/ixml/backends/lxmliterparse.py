# Third-party apps
from lxml import etree  # http://lxml.de/

from ..builders.dictbuilder import DictObjectBuilder

# API
__all__ = ['parse', 'items']


# Params to use in the lxml parser.
# strip_cdata: replace CDATA sections by normal text content.
# remove_blank_text: discard blank text nodes between tags, also known as
# ignorable whitespace.
_parser_params = {
    'strip_cdata': False,
    'remove_blank_text': True,
}


def parse(data, parser_kwargs=_parser_params):

    # Setup the iterator from lxml
    events = ('start', 'end')
    context = etree.iterparse(data, events=events, **parser_kwargs)
    events_elems = fast_iter(context)  # it makes sure Elements are cleared

    # A stack to store the tags while parsing to track the path
    tags = []

    # Variable to store the previous event
    prev = None

    for event, elem in events_elems:

        if event == 'start':

            # Yield the previous one
            if prev is not None:
                yield prev[0], prev[1], prev[2]
                # Yield the attributes
                for attr in prev[3]:
                    yield attr

            # Update the tags
            tags.append(ns_prefixed_tag(el=elem))

            # Update prev
            path = '.'.join(tags)
            prev = (path, event, elem.text, list(iter_attributes(path, elem)))

        elif event == 'end':

            path = '.'.join(tags)

            # If the previous 'start' event has the same path then it is a
            # leaf: yield the value
            if prev is not None and prev[0] == path:
                yield path, 'data', elem.text
                # Yield the attributes
                for attr in prev[3]:
                    yield attr
                # Delete it
                prev = None

            # Otherwise yield the normal 'end' event
            else:
                yield path, event, elem.text

            # Update the tags
            tags.pop()


def iter_attributes(path, el):
    for name, value in el.attrib.iteritems():
        yield '{}.@{}'.format(path, name), 'data', value


def items(data, path, builder_klass=DictObjectBuilder):

    context = parse(data)
    try:
        while True:
            current, event, value = next(context)

            # Build objects only under a specific path
            if current == path:
                if event == 'start':
                    # Init the builder
                    builder = builder_klass(path)

                    # The end event to seek
                    end_event = event.replace('start', 'end')

                    # Get next one and loop until the end event shows up
                    current, event, value = next(context)
                    while (current, event) != (path, end_event):
                        builder.event(current, event, value)
                        current, event, value = next(context)

                    # Yield the constructed object
                    yield builder.value

                else:
                    yield value

    except StopIteration:
        pass


#
# HELPERS
#

def fast_iter(context):
    """
    A fast way to iter since the elements are deleted right after their 'end' event is yield.
    References: http://www.ibm.com/developerworks/xml/library/x-hiperfparse/

    """
    for event, elem in context:
        yield event, elem
        # Can clear ONLY when it's the end of an element
        if event == 'end':
            clear_element(elem)
    # Make sure all elements are cleared
    context.root.clear()
    del context


def clear_element(el):
    el.clear()  # clean up the element and childrens
    while el.getprevious() is not None:
        del el.getparent()[0]  # clean up preceding siblings


def ns_prefixed_tag(el=None, prefix=None, tag=None):
    """Returns a namespace prefixed tag given an Element or its prefix and tag values.

    >>> ns_prefixed_tag(prefix=None, tag='tag_name')
    'tag_name'

    >>> ns_prefixed_tag(prefix=None, tag='{http://www.defaultns.com}tag_name')
    'tag_name'

    >>> ns_prefixed_tag(prefix='prefix', tag='{http://www.ns.com}tag_name')
    'prefix:tag_name'

    >>> ns_prefixed_tag(prefix='prefix', tag='tag_name')
    'prefix:tag_name'


    Examples with an Element and namespaces (default and prefixed).

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
    >>> from lxml import etree; import StringIO
    >>> data = StringIO.StringIO(xml); t = etree.parse(data)
    >>> channel = t.find('channel')
    >>> items = list(channel.iterchildren())

    >>> ns_prefixed_tag(el=items[0])
    'item'
    
    >>> ns_prefixed_tag(el=items[0].getchildren()[0])
    'title'
    
    >>> ns_prefixed_tag(el=items[1])
    'item'
    
    >>> ns_prefixed_tag(el=items[1].getchildren()[0])
    'ns2:title'
    
    """
    # It is an Element, do a recursive call
    if el is not None:
        return ns_prefixed_tag(prefix=el.prefix, tag=el.tag)

    # Removes namespace in {namespace}tag_name
    tag_name = get_tag_name(tag)

    # Only tag name
    if prefix is None:
        return tag_name

    # Prefix and tag name
    return '{0}:{1}'.format(prefix, tag_name)


def get_tag_name(tag):
    """Returns only the tag name of:
        - an Element tag value (that can include the URI namespace)
        - a namespace prefixed tag

    >>> get_tag_name('tag_name')
    'tag_name'

    >>> get_tag_name('{http://www.ns.com}tag_name')
    'tag_name'

    >>> get_tag_name('ns1:tag_name')
    'tag_name'

    """
    if tag[0] == '{':
        return tag.split('}')[-1]

    if ':' in tag:
        return tag.split(':')[1]

    return tag
