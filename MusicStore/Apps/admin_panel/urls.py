from django.urls import path
from . import views

urlpatterns = [
    # Главная страница админ-панели
    path('', views.admin_dashboard, name='admin_dashboard'),
    
    # Товары
    path('products/', views.admin_products, name='admin_products'),
    path('products/create/', views.admin_product_create, name='admin_product_create'),
    path('products/<int:product_id>/', views.admin_product_edit, name='admin_product_edit'),
    path('products/<int:product_id>/delete/', views.admin_product_delete, name='admin_product_delete'),
    path('products/<int:product_id>/add-image/', views.admin_product_add_image, name='admin_product_add_image'),
    path('products/<int:product_id>/add-characteristic/', views.admin_product_add_characteristic, name='admin_product_add_characteristic'),
    path('products/<int:product_id>/delete-image/<int:image_id>/', views.admin_product_delete_image, name='admin_product_delete_image'),
    path('products/<int:product_id>/delete-characteristic/<int:characteristic_id>/', views.admin_product_delete_characteristic, name='admin_product_delete_characteristic'),
    
    # Категории
    path('categories/', views.admin_categories, name='admin_categories'),
    path('categories/create/', views.admin_category_create, name='admin_category_create'),
    path('categories/<int:category_id>/', views.admin_category_edit, name='admin_category_edit'),
    path('categories/<int:category_id>/delete/', views.admin_category_delete, name='admin_category_delete'),
    
    # Бренды
    path('brands/', views.admin_brands, name='admin_brands'),
    path('brands/create/', views.admin_brand_create, name='admin_brand_create'),
    path('brands/<int:brand_id>/', views.admin_brand_edit, name='admin_brand_edit'),
    path('brands/<int:brand_id>/delete/', views.admin_brand_delete, name='admin_brand_delete'),
    
    # Заказы
    path('orders/', views.admin_orders, name='admin_orders'),
    path('orders/<int:order_id>/', views.admin_order_detail, name='admin_order_detail'),
    path('orders/<int:order_id>/delete/', views.admin_order_delete, name='admin_order_delete'),
    
    # Пользователи
    path('users/', views.admin_users, name='admin_users'),
    path('users/<int:user_id>/', views.admin_user_detail, name='admin_user_detail'),
    
    # Статусы заказов
    path('order-statuses/', views.admin_order_statuses, name='admin_order_statuses'),
    path('order-statuses/create/', views.admin_order_status_create, name='admin_order_status_create'),
    path('order-statuses/<int:status_id>/', views.admin_order_status_edit, name='admin_order_status_edit'),
    path('order-statuses/<int:status_id>/delete/', views.admin_order_status_delete, name='admin_order_status_delete'),
    
    # Способы оплаты
    path('payment-methods/', views.admin_payment_methods, name='admin_payment_methods'),
    path('payment-methods/create/', views.admin_payment_method_create, name='admin_payment_method_create'),
    path('payment-methods/<int:method_id>/', views.admin_payment_method_edit, name='admin_payment_method_edit'),
    path('payment-methods/<int:method_id>/delete/', views.admin_payment_method_delete, name='admin_payment_method_delete'),
    
    # Способы доставки
    path('delivery-methods/', views.admin_delivery_methods, name='admin_delivery_methods'),
    path('delivery-methods/create/', views.admin_delivery_method_create, name='admin_delivery_method_create'),
    path('delivery-methods/<int:method_id>/', views.admin_delivery_method_edit, name='admin_delivery_method_edit'),
    path('delivery-methods/<int:method_id>/delete/', views.admin_delivery_method_delete, name='admin_delivery_method_delete'),
    
    # Отзывы
    path('reviews/', views.admin_reviews, name='admin_reviews'),
    path('reviews/<int:review_id>/approve/', views.admin_review_approve, name='admin_review_approve'),
    path('reviews/<int:review_id>/reject/', views.admin_review_reject, name='admin_review_reject'),
    path('reviews/<int:review_id>/delete/', views.admin_review_delete, name='admin_review_delete'),
    
    # Аналитика
    path('analytics/', views.admin_analytics, name='admin_analytics'),
    path('analytics/export-pdf/', views.admin_analytics_export_pdf, name='admin_analytics_export_pdf'),
]

