import logging
import datetime

from django.db import transaction
from django.utils import timezone

from sv_base.utils.common.utext import md5, sha1
from sv_base.utils.tools.http import HttpClient

from sv_auth.models import User

from sv_we import app_settings
from sv_we.models import WeAppInfo, WeUser


logger = logging.getLogger(__name__)


def get_access_token(app_id):
    app_info = WeAppInfo.objects.filter(app_id=app_id).first()
    if not _valid_access_token(app_info):
        ret = pull_access_token(app_id)
        access_token = ret['access_token']
        expires_in = ret['expires_in']
        expire_time = timezone.now() + datetime.timedelta(seconds=expires_in)
        if not app_info:
            app_info = WeAppInfo(app_id=app_id)
        app_info.access_token = access_token
        app_info.access_token_expire_time = expire_time
        app_info.save()

    return app_info.access_token


def _valid_access_token(app_info):
    if not app_info:
        return False

    if app_info.access_token_expire_time <= timezone.now():
        logger.info('app access token expired')
        return False

    return True


def pull_access_token(app_id):
    http = HttpClient()
    app_access_token_url = app_settings.APPS[app_id]['APP_ACCESS_TOKEN_URL']
    ret = http.jget(app_access_token_url)
    print(ret)
    return ret


def sync_openid(openid):
    if not openid:
        return None

    if not WeUser.objects.filter(openid=openid).exists():
        with transaction.atomic():
            user = User.objects.create(username=openid)
            WeUser.objects.create(
                user=user,
                openid=openid,
                openid_key=md5(openid),
            )


def is_we_access(app_id, signature, timestamp, nonce):
    token = app_settings.APPS[app_id]['TOKEN']

    try:
        signature_list = sorted([token, timestamp, nonce])
        calc_signature = sha1(''.join(signature_list))
    except Exception:
        return False
    else:
        if calc_signature == signature:
            return True

    return False
