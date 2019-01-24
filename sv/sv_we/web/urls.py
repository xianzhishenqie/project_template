
from django.urls import path

from . import views


urlpatterns = [
    path('access/<slug:app_id>/', views.we_access, name='access'),
]

