from django.urls import path
from . import views

urlpatterns = [
    path('', views.orders_view, name='orders'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('success/<int:order_id>/', views.order_success_view, name='order_success'),
    path('cancel/<int:order_id>/', views.cancel_order_view, name='cancel_order'),
]

