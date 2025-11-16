from rest_framework import viewsets
from .models import Users, Roles, Userroles, Addresses
from .serializers import UserSerializer, RoleSerializer, UserRoleSerializer, AddressSerializer


class UsersViewSet(viewsets.ModelViewSet):
    queryset = Users.objects.all()
    serializer_class = UserSerializer


class RolesViewSet(viewsets.ModelViewSet):
    queryset = Roles.objects.all()
    serializer_class = RoleSerializer


class UserRolesViewSet(viewsets.ModelViewSet):
    queryset = Userroles.objects.all()
    serializer_class = UserRoleSerializer


class AddressesViewSet(viewsets.ModelViewSet):
    queryset = Addresses.objects.all()
    serializer_class = AddressSerializer


