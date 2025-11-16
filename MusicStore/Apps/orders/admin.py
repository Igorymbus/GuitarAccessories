from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Orderstatuses, Orders, Orderitems, Orderhistory


@admin.register(Orderstatuses)
class OrderStatusesAdmin(admin.ModelAdmin):
    """Административная панель для статусов заказов"""
    list_display = ("order_statuses_id", "order_statuses_name", "get_orders_count")
    search_fields = ("order_statuses_name",)
    list_display_links = ("order_statuses_id", "order_statuses_name")
    ordering = ("order_statuses_id",)
    
    def get_orders_count(self, obj):
        """Количество заказов со статусом"""
        count = Orders.objects.filter(orders_status=obj).count()
        return count
    get_orders_count.short_description = 'Количество заказов'


class OrderItemInline(admin.TabularInline):
    """Встроенная форма для товаров заказа"""
    model = Orderitems
    extra = 0
    fields = ('order_items_product', 'order_items_quantity', 'order_items_price_at_purchase', 'item_total')
    readonly_fields = ('order_items_price_at_purchase', 'item_total')
    
    def item_total(self, obj):
        """Общая стоимость позиции"""
        if obj and obj.order_items_quantity and obj.order_items_price_at_purchase:
            total = obj.order_items_quantity * obj.order_items_price_at_purchase
            return format_html('<strong>{:.2f} ₽</strong>', total)
        return "—"
    item_total.short_description = 'Сумма'


@admin.register(Orders)
class OrdersAdmin(admin.ModelAdmin):
    """Административная панель для заказов"""
    list_display = (
        "orders_id", 
        "orders_user", 
        "orders_date", 
        "orders_status", 
        "orders_total_amount",
        "order_status_color",
        "get_items_count",
        "user_link"
    )
    list_filter = ("orders_status", "orders_date", "orders_payment_method", "orders_delivery_method")
    search_fields = ("orders_id", "orders_user__users_email", "orders_user__users_first_name", "orders_user__users_last_name")
    list_display_links = ("orders_id",)
    date_hierarchy = "orders_date"
    ordering = ("-orders_date",)
    inlines = [OrderItemInline]
    readonly_fields = ("orders_date", "orders_total_amount", "user_link")
    actions = ['mark_as_processing', 'mark_as_sent', 'mark_as_delivered']
    
    fieldsets = (
        ('Информация о заказе', {
            'fields': ('orders_user', 'user_link', 'orders_status', 'orders_date', 'orders_total_amount')
        }),
        ('Доставка и оплата', {
            'fields': ('orders_delivery_method', 'orders_payment_method', 'orders_address')
        }),
        ('Комментарий', {
            'fields': ('orders_comment',),
            'classes': ('collapse',)
        }),
    )
    
    def order_status_color(self, obj):
        """Цветовая индикация статуса заказа"""
        if obj.orders_status:
            status_name = obj.orders_status.order_statuses_name
            colors = {
                'Новый': '#007bff',
                'В обработке': '#ffc107',
                'Отправлен': '#6f42c1',
                'Доставлен': '#28a745',
                'Отменен': '#dc3545',
            }
            color = colors.get(status_name, '#6c757d')
            return format_html(
                '<span style="color: {}; font-weight: bold; padding: 4px 8px; background: {}20; border-radius: 4px;">{}</span>',
                color, color, status_name
            )
        return "—"
    order_status_color.short_description = 'Статус'
    
    def get_items_count(self, obj):
        """Количество товаров в заказе"""
        count = Orderitems.objects.filter(order_items_order=obj).count()
        return format_html('<strong>{}</strong>', count)
    get_items_count.short_description = 'Товаров'
    
    def user_link(self, obj):
        """Ссылка на пользователя"""
        if obj and obj.orders_user:
            url = reverse('admin:users_users_change', args=[obj.orders_user.users_id])
            return format_html('<a href="{}">{} {}</a>', url, obj.orders_user.users_first_name, obj.orders_user.users_last_name)
        return "—"
    user_link.short_description = 'Пользователь'
    
    @admin.action(description='Отметить как "В обработке"')
    def mark_as_processing(self, request, queryset):
        from .models import Orderstatuses
        status = Orderstatuses.objects.filter(order_statuses_name='В обработке').first()
        if status:
            updated = queryset.update(orders_status=status)
            self.message_user(request, f'{updated} заказов отмечено как "В обработке".')
    
    @admin.action(description='Отметить как "Отправлен"')
    def mark_as_sent(self, request, queryset):
        from .models import Orderstatuses
        status = Orderstatuses.objects.filter(order_statuses_name='Отправлен').first()
        if status:
            updated = queryset.update(orders_status=status)
            self.message_user(request, f'{updated} заказов отмечено как "Отправлен".')
    
    @admin.action(description='Отметить как "Доставлен"')
    def mark_as_delivered(self, request, queryset):
        from .models import Orderstatuses
        status = Orderstatuses.objects.filter(order_statuses_name='Доставлен').first()
        if status:
            updated = queryset.update(orders_status=status)
            self.message_user(request, f'{updated} заказов отмечено как "Доставлен".')


@admin.register(Orderitems)
class OrderItemsAdmin(admin.ModelAdmin):
    """Административная панель для товаров в заказах"""
    list_display = ("order_items_id", "order_items_order", "order_items_product", "order_items_quantity", "order_items_price_at_purchase", "get_total")
    list_filter = ("order_items_order__orders_status", "order_items_order__orders_date")
    search_fields = ("order_items_order__orders_id", "order_items_product__products_name")
    list_display_links = ("order_items_id", "order_items_order")
    ordering = ("-order_items_order__orders_date",)
    
    def get_total(self, obj):
        """Общая стоимость позиции"""
        total = obj.order_items_quantity * obj.order_items_price_at_purchase
        return f"{total:.2f} ₽"
    get_total.short_description = 'Сумма'


@admin.register(Orderhistory)
class OrderHistoryAdmin(admin.ModelAdmin):
    """Административная панель для истории заказов"""
    list_display = ("order_history_id", "order_history_order", "order_history_status", "order_history_changed_at", "order_history_changed_by")
    list_filter = ("order_history_status", "order_history_changed_at")
    search_fields = ("order_history_order__orders_id", "order_history_changed_by__users_email")
    list_display_links = ("order_history_id", "order_history_order")
    date_hierarchy = "order_history_changed_at"
    ordering = ("-order_history_changed_at",)
    readonly_fields = ("order_history_changed_at",)
