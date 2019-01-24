
from rest_framework_xml.parsers import XMLParser


class TextXMLParser(XMLParser):
    
    media_type = 'text/xml'