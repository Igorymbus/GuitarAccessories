from rest_framework import viewsets
from .models import Carts, Cartitems
from .serializers import CartSerializer, CartItemSerializer


class CartsViewSet(viewsets.ModelViewSet):
    queryset = Carts.objects.all()
    serializer_class = CartSerializer


class CartItemsViewSet(viewsets.ModelViewSet):
    queryset = Cartitems.objects.all()
    serializer_class = CartItemSerializer


