from rest_framework_xml.renderers import XMLRenderer


class TextXMLRenderer(XMLRenderer):
    """
    xml响应渲染器
    """
    media_type = 'text/xml'
