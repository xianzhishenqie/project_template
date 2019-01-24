
import functools

from django.contrib.auth import login

from sv_base.utils import views as default_views

from sv_we import models as we_models


def auto_login(ignore=False):
    def wrapper(func):
        @functools.wraps(func)
        def _wrapper(request, *args, **kwargs):
            openid_key = request.GET.get('key')
            if request.user.is_authenticated:
                if openid_key and request.user.weuser.openid_key != openid_key:
                    we_user = we_models.WeUser.objects.filter(openid_key=openid_key).first()
                    if we_user:
                        login(request, we_user.user)
            else:
                if not openid_key and not ignore:
                    return default_views.Http403Page(request)

                we_user = we_models.WeUser.objects.filter(openid_key=openid_key).first()
                if we_user:
                    login(request, we_user.user)
                else:
                    if not ignore:
                        return default_views.Http403Page(request)
            return func(request, *args, **kwargs)
        return _wrapper
    return wrapper
