
import logging

from sv_base.utils.tools.http import HttpClient

from sv_we import setting
from sv_we.utils import common


logger = logging.getLogger(__name__)


def create_menus(app_id, menus):
    access_token = common.get_access_token(app_id)
    app_menu_create_url = setting.APPS[app_id]['APP_MENU_CREATE_URL']
    http = HttpClient()
    ret = http.jpost(app_menu_create_url.format(access_token=access_token), data=menus)
    return ret
