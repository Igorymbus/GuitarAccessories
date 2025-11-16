from rest_framework import serializers
from .models import Paymentmethods, Deliverymethods, Payments


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paymentmethods
        fields = '__all__'


class DeliveryMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deliverymethods
        fields = '__all__'


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payments
        fields = '__all__'



