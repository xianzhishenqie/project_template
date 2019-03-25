import logging

from django.utils.module_loading import import_string
from django.views.decorators.csrf import csrf_exempt

from rest_framework.decorators import api_view, permission_classes, parser_classes, renderer_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from sv_base.utils.rest.decorators import request_data
from sv_base.utils.rest.parsers import TextXMLParser

from sv_we import setting
from sv_we.utils import common
from sv_we.utils.rest.renderers import CDATATextXMLRenderer


logger = logging.getLogger(__name__)


@api_view(['GET', 'POST'])
@permission_classes((AllowAny,))
@parser_classes((TextXMLParser,))
@renderer_classes((CDATATextXMLRenderer,))
@csrf_exempt
@request_data()
def we_access(request, app_id):
    app_config = setting.APPS.get(app_id)
    if not app_config:
        return Response('')

    signature = request.query_data.get('signature')
    timestamp = request.query_data.get('timestamp')
    nonce = request.query_data.get('nonce')
    echostr = request.query_data.get('echostr')

    if request.method == 'GET':
        if not common.is_we_access(app_id, signature, timestamp, nonce):
            echostr = ''

        return Response(echostr)
    elif request.method == 'POST':
        if not common.is_we_access(app_id, signature, timestamp, nonce):
            return Response(echostr)

        openid = request.query_data.get('openid')
        common.sync_openid(openid)

        try:
            handler = import_string(app_config['USER_MESSAGE_HANDLER'])(request.shift_data)
            echostr = handler.handle()
        except Exception as e:
            logger.error('handle msg error: %s', e)
            echostr = ''

        return Response(echostr)
