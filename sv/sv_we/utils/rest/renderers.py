
from lxml.etree import CDATA, Element, tostring

from django.utils import six
from django.utils.encoding import smart_text

from sv_base.utils.common.utext import dc
from sv_base.utils.rest.renderers import TextXMLRenderer


class CDATATextXMLRenderer(TextXMLRenderer):

    item_tag_name = 'item'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if not data:
            return ''

        if not isinstance(data, (tuple, list, dict)):
            return data

        tags = []
        self._to_xml(tags, data)
        xml = '<xml>{}</xml>'.format(''.join(tags))

        return xml

    def _to_xml(self, tags, data):
        if isinstance(data, (tuple, list)):
            for d in data:
                tags.append('<{}>'.format(self.item_tag_name))
                self._to_xml(tags, d)
                tags.append('</{}>'.format(self.item_tag_name))
        elif isinstance(data, dict):
            for key, value in data.items():
                tags.append('<{}>'.format(key))
                self._to_xml(tags, value)
                tags.append('</{}>'.format(key))
        elif data is None:
            pass
        else:
            tags.append(self._cdata(data))


    def _cdata(self, text):
        if isinstance(text, six.string_types):
            el = Element('a')
            el.text = CDATA(text)
            return dc(tostring(el)[3:-4])

        return smart_text(text)
