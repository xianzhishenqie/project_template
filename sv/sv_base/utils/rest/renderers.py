from rest_framework_xml.renderers import XMLRenderer


class TextXMLRenderer(XMLRenderer):

    media_type = 'text/xml'
