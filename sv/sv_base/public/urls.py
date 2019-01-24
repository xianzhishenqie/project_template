
from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static

from . import rest_views


apiurlpatterns = [
    url(r'^csrf_token/$', rest_views.csrf_token, name='csrf_token'),
]


urlpatterns = static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
