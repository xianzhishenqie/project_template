from sv_we import app_settings


def add_app(app_id, app_config):
    complete_app_config(app_id, app_config)
    app_settings.APPS[app_id] = app_config


def complete_app_config(app_id, app_config):
    app_secret = app_config.get('APP_SECRET')
    app_config.update({
        'APP_MENU_CREATE_URL': 'https://api.weixin.qq.com/cgi-bin/menu/create'
                               '?access_token={access_token}',
        'APP_ACCESS_TOKEN_URL': 'https://api.weixin.qq.com/cgi-bin/token'
                                f'?appid={app_id}&secret={app_secret}'
                                '&grant_type=client_credential',
        'SILENT_CODE_URL': 'https://open.weixin.qq.com/connect/oauth2/authorize'
                           f'?appid={app_id}'
                           '&redirect_uri={redirect_uri}'
                           '&response_type=code&scope=snsapi_base&state=123#wechat_redirect',
        'ACCESS_TOKEN_URL': 'https://api.weixin.qq.com/sns/oauth2/access_token'
                            f'?appid={app_id}&secret={app_secret}'
                            '&code={code}'
                            '&grant_type=authorization_code',
    })
