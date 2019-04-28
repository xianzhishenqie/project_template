from django.contrib.auth import authenticate, login

from rest_framework import exceptions, filters, status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from sv_base.utils.base.text import rk
from sv_base.extensions.rest.mixins import CacheModelMixin, BatchSetModelMixin, DestroyModelMixin, SVMixin

from sv_auth.extensions.rest.decorators import org_queryset
from sv_auth.extensions.rest.permissions import IsAdminOrReadOnly
from sv_auth.models import Organization, User
from sv_auth.utils import org as org_util

from . import serializers as mserializers
from .error import Error


class SessionViewSet(SVMixin, viewsets.GenericViewSet):
    permission_classes = (AllowAny,)
    serializer_class = mserializers.UserSerializer

    def create(self, request):
        username = self.shift_data.get('username')
        password = self.shift_data.get('password')
        user = authenticate(username=username, password=password)
        if not user:
            raise exceptions.AuthenticationFailed(Error.AUTHENTICATION_FAILED)
        login(request, user)
        return Response(status=status.HTTP_200_OK)


class OrganizationViewSet(CacheModelMixin, SVMixin, viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = mserializers.OrganizationSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('name',)
    ordering_fields = ('id',)
    ordering = ('id',)
    unlimit_pagination = True

    def sub_perform_create(self, serializer):
        validated_data = serializer.validated_data
        if not org_util.can_add_org(self.request.user, validated_data.get('parent')):
            raise exceptions.PermissionDenied(Error.NO_PERMISSION)

        return super(OrganizationViewSet, self).sub_perform_create(serializer)

    def sub_perform_update(self, serializer):
        if not org_util.can_operate_org(self.request.user, serializer.instance):
            raise exceptions.PermissionDenied(Error.NO_PERMISSION)

        return super(OrganizationViewSet, self).sub_perform_update(serializer)

    def sub_perform_destroy(self, instance):
        if not org_util.can_operate_org(self.request.user, instance):
            raise exceptions.PermissionDenied(Error.NO_PERMISSION)

        return super(OrganizationViewSet, self).sub_perform_destroy(instance)


class UserViewSet(BatchSetModelMixin, DestroyModelMixin, CacheModelMixin, SVMixin, viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = mserializers.UserSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('username', 'nickname', 'name')
    ordering_fields = ('id',)
    ordering = ('-id',)

    @org_queryset
    def get_queryset(self):
        queryset = self.queryset

        exclude = self.query_data.getlist('exclude', int)
        if exclude:
            queryset = queryset.exclude(pk__in=exclude)

        organization = self.query_data.get('organization', int)
        if organization is not None:
            queryset = queryset.filter(organization=organization)

        group = self.query_data.getlist('group', User.Group.__members__.values())
        if group:
            queryset = queryset.filter(groups=group)

        return queryset

    def sub_perform_create(self, serializer):
        validated_data = serializer.validated_data
        if not org_util.can_add_user(
                self.request.user,
                validated_data.get('organization'),
                validated_data.get('groups')
        ):
            raise exceptions.PermissionDenied(Error.NO_PERMISSION)

        return super(UserViewSet, self).sub_perform_create(serializer)

    def sub_perform_update(self, serializer):
        if not org_util.can_operate_user(self.request.user, serializer.instance):
            raise exceptions.PermissionDenied(Error.NO_PERMISSION)

        return super(UserViewSet, self).sub_perform_update(serializer)

    def sub_perform_destroy(self, serializer):
        raise exceptions.PermissionDenied()

    def perform_batch_destroy(self, queryset):
        queryset = org_util.filter_org_queryset(self.request.user, queryset)

        deleted_users = []
        for instance in queryset:
            if not org_util.can_operate_user(self.request.user, instance):
                continue
            instance.status = User.Status.DELETE
            random_key = rk()
            instance.username = random_key
            instance.email = random_key
            instance.save()
            deleted_users.append(instance)
        if deleted_users:
            return True
        return False
