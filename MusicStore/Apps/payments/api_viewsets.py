from rest_framework import viewsets
from .models import Paymentmethods, Deliverymethods, Payments
from .serializers import PaymentMethodSerializer, DeliveryMethodSerializer, PaymentSerializer


class PaymentMethodsViewSet(viewsets.ModelViewSet):
    queryset = Paymentmethods.objects.all()
    serializer_class = PaymentMethodSerializer


class DeliveryMethodsViewSet(viewsets.ModelViewSet):
    queryset = Deliverymethods.objects.all()
    serializer_class = DeliveryMethodSerializer


class PaymentsViewSet(viewsets.ModelViewSet):
    queryset = Payments.objects.all()
    serializer_class = PaymentSerializer


