from django.urls import path
from . import views

urlpatterns = [
    path('', views.catalog_view, name='catalog'),
    path('product/<int:product_id>/', views.product_detail_view, name='product_detail'),
    path('favorites/', views.favorites_view, name='favorites'),
    path('favorites/add/<int:product_id>/', views.add_to_favorites, name='add_to_favorites'),
    path('favorites/remove/<int:product_id>/', views.remove_from_favorites, name='remove_from_favorites'),
]

