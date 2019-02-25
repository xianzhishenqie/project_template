# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

SERVER = 'http://www.shixiaobo.com'

# app名称 url路径
SV_APP_PATHS = [
    ('sv_base', ''),
    'sv_auth',
    'sv_we',
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
