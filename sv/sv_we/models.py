from django.db import models

from sv_auth.models import User


class WeAppInfo(models.Model):
    app_id = models.CharField(max_length=100, unique=True)
    access_token = models.CharField(max_length=1024)
    access_token_expire_time = models.DateTimeField()


class WeUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    openid = models.CharField(max_length=100)
    openid_key = models.CharField(max_length=100)
