from django.urls import path

from sv_auth import app_settings

from . import api


viewsets = [
    api.UserViewSet,
]

if app_settings.ENABLE_ORG:
    viewsets.append(api.OrganizationViewSet)


apiurlpatterns = [
    path('login/', api.SessionViewSet.as_view({'post': 'create'}), name='login'),
]
