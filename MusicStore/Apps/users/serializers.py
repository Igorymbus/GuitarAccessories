from rest_framework import serializers
from .models import Users, Roles, Userroles, Addresses


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roles
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = '__all__'


class UserRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Userroles
        fields = '__all__'


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Addresses
        fields = '__all__'



