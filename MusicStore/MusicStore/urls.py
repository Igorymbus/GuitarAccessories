"""
URL configuration for MusicStore project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
# Импортируем настройки админ-панели для применения заголовков
import main.admin
from main import views as main_views
from rest_framework.routers import DefaultRouter
from Apps.catalog.api import ProductViewSet, CategoryViewSet, BrandViewSet
from Apps.users.api_viewsets import UsersViewSet, RolesViewSet, UserRolesViewSet, AddressesViewSet
from Apps.cart.api_viewsets import CartsViewSet, CartItemsViewSet
from Apps.orders.api_viewsets import OrderStatusesViewSet, OrdersViewSet, OrderItemsViewSet, OrderHistoryViewSet
from Apps.payments.api_viewsets import PaymentMethodsViewSet, DeliveryMethodsViewSet, PaymentsViewSet
from Apps.extras.api_viewsets import ReviewsViewSet, FeedbackViewSet, AnalyticsViewSet
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from Apps.users.api import RegisterAPIView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('Apps.users.urls')),
    # Корневой: анонимов ведем на регистрацию, авторизованных на home
    path('', include('Apps.users.urls')),
    path('home/', main_views.home, name='home'),
    path('catalog/', include('Apps.catalog.urls')),
    path('cart/', include('Apps.cart.urls')),
    path('orders/', include('Apps.orders.urls')),
    # Админ-панель сайта
    path('admin-panel/', include('Apps.admin_panel.urls')),
    # API
    path('api/auth/register/', RegisterAPIView.as_view(), name='api-register'),
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

# Router for read-only catalog
router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'brands', BrandViewSet, basename='brand')
router.register(r'users', UsersViewSet, basename='users')
router.register(r'roles', RolesViewSet, basename='roles')
router.register(r'userroles', UserRolesViewSet, basename='userroles')
router.register(r'addresses', AddressesViewSet, basename='addresses')
router.register(r'carts', CartsViewSet, basename='carts')
router.register(r'cartitems', CartItemsViewSet, basename='cartitems')
router.register(r'orderstatuses', OrderStatusesViewSet, basename='orderstatuses')
router.register(r'orders', OrdersViewSet, basename='orders')
router.register(r'orderitems', OrderItemsViewSet, basename='orderitems')
router.register(r'orderhistory', OrderHistoryViewSet, basename='orderhistory')
router.register(r'paymentmethods', PaymentMethodsViewSet, basename='paymentmethods')
router.register(r'deliverymethods', DeliveryMethodsViewSet, basename='deliverymethods')
router.register(r'payments', PaymentsViewSet, basename='payments')
router.register(r'reviews', ReviewsViewSet, basename='reviews')
router.register(r'feedback', FeedbackViewSet, basename='feedback')
router.register(r'analytics', AnalyticsViewSet, basename='analytics')

urlpatterns += [
    path('api/', include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
