# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

PUBLIC_SERVER_PROTOCOL = 'http'
PUBLIC_SERVER_IP = '127.0.0.1'
PUBLIC_SERVER_PORT = 80

SERVER_PROTOCOL = 'http'
SERVER_IP = '127.0.0.1'
SERVER_PORT = 8077


# app名称 url路径
SV_APP_PATHS = [
    ('sv_base', ''),
    'sv_auth',
]


# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'sv',
        'USER': 'sv',
        'PASSWORD': 'sv',
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}


# app配置
APP_SETTINGS = {

}
