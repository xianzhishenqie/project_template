
from rest_framework_xml.parsers import XMLParser


class TextXMLParser(XMLParser):
    """
    xml请求解析器
    """
    media_type = 'text/xml'
