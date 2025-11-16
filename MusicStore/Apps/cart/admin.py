from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Carts, Cartitems


class CartItemInline(admin.TabularInline):
    """Встроенная форма для товаров в корзине"""
    model = Cartitems
    extra = 0
    fields = ('cart_items_product', 'cart_items_quantity', 'item_price', 'item_total')
    readonly_fields = ('item_price', 'item_total')
    
    def item_price(self, obj):
        """Цена товара"""
        if obj and obj.cart_items_product:
            price = float(obj.cart_items_product.products_price)
            price_display = f"{price:.2f} ₽"
            return format_html('<strong>{}</strong>', price_display)
        return "—"
    item_price.short_description = 'Цена'
    
    def item_total(self, obj):
        """Общая стоимость позиции"""
        if obj and obj.cart_items_product and obj.cart_items_quantity:
            total = obj.cart_items_quantity * float(obj.cart_items_product.products_price)
            total_display = f"{total:.2f} ₽"
            return format_html('<strong>{}</strong>', total_display)
        return "—"
    item_total.short_description = 'Сумма'


@admin.register(Carts)
class CartsAdmin(admin.ModelAdmin):
    """Административная панель для корзин"""
    list_display = ("carts_id", "carts_user", "carts_created_at", "get_items_count", "get_total_amount", "user_link")
    list_filter = ("carts_created_at",)
    search_fields = ("carts_user__users_email", "carts_user__users_first_name", "carts_user__users_last_name")
    list_display_links = ("carts_id", "carts_user")
    date_hierarchy = "carts_created_at"
    ordering = ("-carts_created_at",)
    inlines = [CartItemInline]
    readonly_fields = ("carts_created_at", "user_link")
    
    fieldsets = (
        ('Информация о корзине', {
            'fields': ('carts_user', 'user_link', 'carts_created_at')
        }),
    )
    
    def get_items_count(self, obj):
        """Количество товаров в корзине"""
        count = Cartitems.objects.filter(cart_items_cart=obj).count()
        return format_html('<strong>{}</strong>', count)
    get_items_count.short_description = 'Товаров'
    
    def get_total_amount(self, obj):
        """Общая стоимость корзины"""
        from django.db.models import Sum, F
        total = Cartitems.objects.filter(cart_items_cart=obj).aggregate(
            total=Sum(F('cart_items_quantity') * F('cart_items_product__products_price'))
        )['total'] or 0
        total_display = f"{float(total):.2f} ₽"
        return format_html('<strong>{}</strong>', total_display)
    get_total_amount.short_description = 'Сумма'
    
    def user_link(self, obj):
        """Ссылка на пользователя"""
        if obj and obj.carts_user:
            url = reverse('admin:users_users_change', args=[obj.carts_user.users_id])
            return format_html('<a href="{}">{} {}</a>', url, obj.carts_user.users_first_name, obj.carts_user.users_last_name)
        return "—"
    user_link.short_description = 'Пользователь'


@admin.register(Cartitems)
class CartItemsAdmin(admin.ModelAdmin):
    """Административная панель для товаров в корзинах"""
    list_display = ("cart_items_id", "cart_items_cart", "cart_items_product", "cart_items_quantity")
    list_filter = ("cart_items_cart__carts_created_at",)
    search_fields = ("cart_items_product__products_name", "cart_items_cart__carts_user__users_email")
    list_display_links = ("cart_items_id", "cart_items_cart")
    ordering = ("-cart_items_cart__carts_created_at",)
