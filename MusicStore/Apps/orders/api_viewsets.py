from rest_framework import viewsets
from .models import Orderstatuses, Orders, Orderitems, Orderhistory
from .serializers import (
    OrderStatusSerializer,
    OrderSerializer,
    OrderItemSerializer,
    OrderHistorySerializer,
)


class OrderStatusesViewSet(viewsets.ModelViewSet):
    queryset = Orderstatuses.objects.all()
    serializer_class = OrderStatusSerializer


class OrdersViewSet(viewsets.ModelViewSet):
    queryset = Orders.objects.all()
    serializer_class = OrderSerializer


class OrderItemsViewSet(viewsets.ModelViewSet):
    queryset = Orderitems.objects.all()
    serializer_class = OrderItemSerializer


class OrderHistoryViewSet(viewsets.ModelViewSet):
    queryset = Orderhistory.objects.all()
    serializer_class = OrderHistorySerializer


