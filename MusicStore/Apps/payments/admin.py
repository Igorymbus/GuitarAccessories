from django.contrib import admin
from django.utils.html import format_html
from .models import Paymentmethods, Deliverymethods, Payments


@admin.register(Paymentmethods)
class PaymentMethodsAdmin(admin.ModelAdmin):
    """Административная панель для способов оплаты"""
    list_display = ("payment_methods_id", "payment_methods_name", "get_orders_count")
    search_fields = ("payment_methods_name",)
    list_display_links = ("payment_methods_id", "payment_methods_name")
    ordering = ("payment_methods_name",)
    
    def get_orders_count(self, obj):
        """Количество заказов с этим способом оплаты"""
        from Apps.orders.models import Orders
        count = Orders.objects.filter(orders_payment_method=obj).count()
        return count
    get_orders_count.short_description = 'Заказов'


@admin.register(Deliverymethods)
class DeliveryMethodsAdmin(admin.ModelAdmin):
    """Административная панель для способов доставки"""
    list_display = ("delivery_methods_id", "delivery_methods_name", "delivery_methods_cost", "get_orders_count")
    search_fields = ("delivery_methods_name", "delivery_methods_description")
    list_display_links = ("delivery_methods_id", "delivery_methods_name")
    list_editable = ("delivery_methods_cost",)
    ordering = ("delivery_methods_name",)
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('delivery_methods_name', 'delivery_methods_description')
        }),
        ('Стоимость', {
            'fields': ('delivery_methods_cost',)
        }),
    )
    
    def get_orders_count(self, obj):
        """Количество заказов с этим способом доставки"""
        from Apps.orders.models import Orders
        count = Orders.objects.filter(orders_delivery_method=obj).count()
        return count
    get_orders_count.short_description = 'Заказов'


@admin.register(Payments)
class PaymentsAdmin(admin.ModelAdmin):
    """Административная панель для платежей"""
    list_display = ("payments_id", "payments_order", "payments_amount", "payments_status", "payments_date", "payment_status_color")
    list_filter = ("payments_status", "payments_date")
    search_fields = ("payments_order__orders_id", "payments_transaction_id")
    list_display_links = ("payments_id", "payments_order")
    date_hierarchy = "payments_date"
    ordering = ("-payments_date",)
    readonly_fields = ("payments_date",)
    
    fieldsets = (
        ('Информация о платеже', {
            'fields': ('payments_order', 'payments_amount', 'payments_status', 'payments_date')
        }),
        ('Детали транзакции', {
            'fields': ('payments_transaction_id',),
            'classes': ('collapse',)
        }),
    )
    
    def payment_status_color(self, obj):
        """Цветовая индикация статуса платежа"""
        status = obj.payments_status.lower() if obj.payments_status else ''
        colors = {
            'pending': 'orange',
            'completed': 'green',
            'failed': 'red',
            'refunded': 'purple',
        }
        color = colors.get(status, 'gray')
        status_display = {
            'pending': 'Ожидает оплаты',
            'completed': 'Оплачен',
            'failed': 'Ошибка',
            'refunded': 'Возврат',
        }.get(status, obj.payments_status or 'Неизвестно')
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, status_display)
    payment_status_color.short_description = 'Статус платежа'
