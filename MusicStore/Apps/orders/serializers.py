from rest_framework import serializers
from .models import Orderstatuses, Orders, Orderitems, Orderhistory


class OrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Orderstatuses
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Orders
        fields = '__all__'


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Orderitems
        fields = '__all__'


class OrderHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Orderhistory
        fields = '__all__'



