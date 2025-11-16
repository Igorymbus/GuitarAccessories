from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Users, Roles, Userroles, Addresses


class UserRoleInline(admin.TabularInline):
    """Встроенная форма для ролей пользователя"""
    model = Userroles
    extra = 0


class AddressInline(admin.TabularInline):
    """Встроенная форма для адресов пользователя"""
    model = Addresses
    extra = 0
    fields = ('addresses_city', 'addresses_street', 'addresses_zip_code', 'addresses_country', 'addresses_is_default')


@admin.register(Users)
class UsersAdmin(admin.ModelAdmin):
    """Административная панель для пользователей"""
    list_display = (
        "users_id", 
        "users_email", 
        "users_full_name", 
        "users_phone", 
        "get_orders_count",
        "get_addresses_count",
        "orders_link"
    )
    list_filter = ("users_created_at",)
    search_fields = ("users_email", "users_first_name", "users_last_name", "users_middle_name", "users_phone")
    list_display_links = ("users_id", "users_email")
    date_hierarchy = "users_created_at"
    ordering = ("-users_created_at",)
    inlines = [UserRoleInline, AddressInline]
    readonly_fields = ("users_created_at", "users_updated_at", "orders_link")
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('users_email', 'users_first_name', 'users_last_name', 'users_middle_name', 'users_phone')
        }),
        ('Безопасность', {
            'fields': ('users_password_hash', 'users_secret_word'),
            'classes': ('collapse',)
        }),
        ('Даты', {
            'fields': ('users_created_at', 'users_updated_at'),
            'classes': ('collapse',)
        }),
        ('Связанные данные', {
            'fields': ('orders_link',),
            'classes': ('collapse',)
        }),
    )
    
    def users_full_name(self, obj):
        """Полное имя пользователя"""
        name_parts = [obj.users_last_name, obj.users_first_name, obj.users_middle_name]
        return ' '.join([part for part in name_parts if part]).strip() or '—'
    users_full_name.short_description = 'ФИО'
    
    def get_orders_count(self, obj):
        """Количество заказов пользователя"""
        from Apps.orders.models import Orders
        count = Orders.objects.filter(orders_user=obj).count()
        return format_html('<strong>{}</strong>', count)
    get_orders_count.short_description = 'Заказов'
    
    def get_addresses_count(self, obj):
        """Количество адресов пользователя"""
        count = Addresses.objects.filter(addresses_user=obj).count()
        return format_html('<strong>{}</strong>', count)
    get_addresses_count.short_description = 'Адресов'
    
    def orders_link(self, obj):
        """Ссылка на заказы пользователя"""
        if obj:
            from Apps.orders.models import Orders
            count = Orders.objects.filter(orders_user=obj).count()
            if count > 0:
                url = reverse('admin:orders_orders_changelist') + f'?orders_user__users_id__exact={obj.users_id}'
                return format_html('<a href="{}">Просмотреть заказы ({})</a>', url, count)
        return "Нет заказов"
    orders_link.short_description = 'Заказы'


@admin.register(Roles)
class RolesAdmin(admin.ModelAdmin):
    """Административная панель для ролей"""
    list_display = ("roles_id", "roles_name", "get_users_count")
    search_fields = ("roles_name",)
    list_display_links = ("roles_id", "roles_name")
    ordering = ("roles_name",)
    
    def get_users_count(self, obj):
        """Количество пользователей с этой ролью"""
        count = Userroles.objects.filter(user_roles_role=obj).count()
        return count
    get_users_count.short_description = 'Пользователей'


@admin.register(Userroles)
class UserRolesAdmin(admin.ModelAdmin):
    """Административная панель для ролей пользователей"""
    list_display = ("user_roles_id", "user_roles_user", "user_roles_role")
    list_filter = ("user_roles_role",)
    search_fields = ("user_roles_user__users_email", "user_roles_user__users_first_name", "user_roles_role__roles_name")
    list_display_links = ("user_roles_id", "user_roles_user")
    ordering = ("user_roles_user", "user_roles_role")


@admin.register(Addresses)
class AddressesAdmin(admin.ModelAdmin):
    """Административная панель для адресов"""
    list_display = ("addresses_id", "addresses_user", "addresses_full_address", "addresses_is_default")
    list_filter = ("addresses_is_default", "addresses_country", "addresses_city")
    search_fields = ("addresses_user__users_email", "addresses_city", "addresses_street", "addresses_zip_code")
    list_display_links = ("addresses_id", "addresses_user")
    list_editable = ("addresses_is_default",)
    ordering = ("-addresses_is_default", "addresses_user")
    
    fieldsets = (
        ('Пользователь', {
            'fields': ('addresses_user', 'addresses_is_default')
        }),
        ('Адрес', {
            'fields': ('addresses_country', 'addresses_city', 'addresses_street', 'addresses_zip_code')
        }),
    )
    
    def addresses_full_address(self, obj):
        """Полный адрес"""
        parts = []
        if obj.addresses_street:
            parts.append(obj.addresses_street)
        if obj.addresses_city:
            parts.append(obj.addresses_city)
        if obj.addresses_zip_code:
            parts.append(obj.addresses_zip_code)
        if obj.addresses_country:
            parts.append(obj.addresses_country)
        return ', '.join(parts) if parts else '—'
    addresses_full_address.short_description = 'Адрес'
