from django.contrib.auth.hashers import make_password

from rest_framework import serializers

from sv_base.extensions.rest.serializers import ModelSerializer

from sv_auth import models as auth_models


class OrganizationSerializer(ModelSerializer):

    parent_data = serializers.SerializerMethodField()

    def get_parent_data(self, obj):
        if obj.parent:
            return OrganizationSerializer(obj.parent).data
        else:
            return None

    class Meta:
        model = auth_models.Organization
        fields = ('id', 'name', 'parent', 'parent_data')


class UserSerializer(ModelSerializer):
    organization_data = serializers.SerializerMethodField()

    def get_organization_data(self, obj):
        if obj.organization:
            return OrganizationSerializer(obj.organization).data
        else:
            return None

    def update(self, instance, validated_data):
        request = self.context.get('request')
        if request and '_clear_groups' in request.data:
            validated_data['groups'] = []

        return super(UserSerializer, self).update(instance, validated_data)

    def to_internal_value(self, data):
        if 'groups' in data:
            if not data.get('groups'):
                data._mutable = True
                data.pop('groups')
                data['_clear_groups'] = True
                data._mutable = False

        password = data.get('password')

        ret = super(UserSerializer, self).to_internal_value(data)

        if password:
            ret['password'] = make_password(password)

        return ret

    class Meta:
        model = auth_models.User
        fields = ('id', 'username', 'logo', 'name', 'organization', 'status',
                  'groups', 'rep_name', 'group', 'organization_data')


class OwnerSerializer(ModelSerializer):
    username = serializers.SerializerMethodField()

    def get_username(self, obj):
        return obj.user.rep_name
