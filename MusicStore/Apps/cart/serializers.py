from rest_framework import serializers
from .models import Carts, Cartitems


class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Carts
        fields = '__all__'


class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cartitems
        fields = '__all__'



