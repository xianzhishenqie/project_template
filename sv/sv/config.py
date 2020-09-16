import os

DEBUG = os.environ.get('DEBUG', 'True').upper() == 'TRUE'

PUBLIC_SERVER_PROTOCOL = 'http'
PUBLIC_SERVER_IP = '127.0.0.1'
PUBLIC_SERVER_PORT = 80

SERVER_PROTOCOL = 'http'
SERVER_IP = '127.0.0.1'
SERVER_PORT = 8077

CORS_ORIGIN_WHITELIST = ()

# app名称 url路径
SV_APP_PATHS = [
    ('sv_base', ''),
    'sv_auth',
]

SERVICE_MODULES = []
if DEBUG:
    SERVICE_MODULES.extend([
        'sv_base.extensions.service.test'
    ])

DEFAULT_FILE_ADDERS = ()

NAMEKO_POOL_SIZE = 100
NAMEKO_MAX_WORKERS = 100

REDIS_HOST = os.environ.get('REDIS_HOST', '127.0.0.1')
REDIS_PORT = os.environ.get('REDIS_PORT', '6379')
REDIS_PASS = os.environ.get('REDIS_PASS', 'v105uCdcjQQuCdgww')

RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST', '127.0.0.1')
RABBITMQ_PORT = os.environ.get('RABBITMQ_PORT', '5672')
RABBITMQ_USER = os.environ.get('RABBITMQ_USER', 'guest')
RABBITMQ_PASS = os.environ.get('RABBITMQ_PASS', 'guest')

FDFS_TRACKER_HOST = os.environ.get('FDFS_TRACKER_HOST', '127.0.0.1')
FDFS_TRACKER_PORT = int(os.environ.get('FDFS_TRACKER_PORT', '22122'))
FDFS_SERVER = os.environ.get('FDFS_SERVER', f'http://{FDFS_TRACKER_HOST}')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'sv'),
        'USER': os.environ.get('DB_USER', 'sv'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'sv'),
        'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
        'PORT': os.environ.get('DB_PORT', '3306'),
        'TEST': {
            'NAME': 'test',
            "CHARSET": "utf8",
            "COLLATION": "utf8_general_ci"
        },
    },
}


# app配置
APP_SETTINGS = {

}
