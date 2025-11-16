from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Categories, Brands, Products, Productimages, Productcharacteristics


@admin.register(Categories)
class CategoryAdmin(admin.ModelAdmin):
    """Административная панель для категорий товаров"""
    list_display = ("categories_id", "categories_name", "categories_parent", "get_products_count", "products_link", "get_children_count")
    list_filter = ("categories_parent",)
    search_fields = ("categories_name", "categories_description")
    list_display_links = ("categories_id", "categories_name")
    ordering = ("categories_name",)
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('categories_name', 'categories_parent', 'categories_description')
        }),
    )
    
    def get_products_count(self, obj):
        """Количество товаров в категории"""
        count = Products.objects.filter(products_category=obj).count()
        return format_html('<strong>{}</strong>', count)
    get_products_count.short_description = 'Товаров'
    
    def get_children_count(self, obj):
        """Количество дочерних категорий"""
        count = Categories.objects.filter(categories_parent=obj).count()
        if count > 0:
            return format_html('<span style="color: #007bff;">{}</span>', count)
        return "—"
    get_children_count.short_description = 'Подкатегорий'
    
    def products_link(self, obj):
        """Ссылка на товары категории"""
        if obj:
            count = Products.objects.filter(products_category=obj).count()
            if count > 0:
                url = reverse('admin:catalog_products_changelist') + f'?products_category__categories_id__exact={obj.categories_id}'
                return format_html('<a href="{}">Просмотреть</a>', url)
        return "—"
    products_link.short_description = 'Действия'


@admin.register(Brands)
class BrandAdmin(admin.ModelAdmin):
    """Административная панель для брендов"""
    list_display = ("brands_id", "brands_logo_preview", "brands_name", "get_products_count", "products_link")
    search_fields = ("brands_name", "brands_description")
    list_display_links = ("brands_id", "brands_name")
    ordering = ("brands_name",)
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('brands_name', 'brands_description', 'logo_preview')
        }),
    )
    
    readonly_fields = ('logo_preview',)
    
    def brands_logo_preview(self, obj):
        """Превью логотипа в списке"""
        if obj and obj.brands_logo_url:
            return format_html(
                '<img src="{}" style="max-height: 40px; max-width: 40px; object-fit: contain;" />',
                obj.brands_logo_url
            )
        return "—"
    brands_logo_preview.short_description = 'Логотип'
    
    def logo_preview(self, obj):
        """Превью логотипа в форме"""
        if obj and obj.brands_logo_url:
            return format_html(
                '<img src="{}" style="max-height: 200px; max-width: 200px; object-fit: contain; border: 1px solid #ddd; padding: 10px; border-radius: 4px;" />',
                obj.brands_logo_url
            )
        return "Логотип не загружен"
    logo_preview.short_description = 'Превью логотипа'
    
    def get_products_count(self, obj):
        """Количество товаров бренда"""
        count = Products.objects.filter(products_brand=obj).count()
        return format_html('<strong>{}</strong>', count)
    get_products_count.short_description = 'Товаров'
    
    def products_link(self, obj):
        """Ссылка на товары бренда"""
        if obj:
            count = Products.objects.filter(products_brand=obj).count()
            if count > 0:
                url = reverse('admin:catalog_products_changelist') + f'?products_brand__brands_id__exact={obj.brands_id}'
                return format_html('<a href="{}">Просмотреть товары ({})</a>', url, count)
        return "—"
    products_link.short_description = 'Действия'


class ProductImageInline(admin.TabularInline):
    """Встроенная форма для изображений товара"""
    model = Productimages
    extra = 1
    fields = ('upload_image', 'product_images_is_main', 'image_preview')
    readonly_fields = ('image_preview',)
    # Дополнительное поле формы (виртуальное) для загрузки файла
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        # Добавляем поле upload_image динамически
        form = formset.form
        if 'upload_image' not in form.base_fields:
            from django import forms
            form.base_fields['upload_image'] = forms.ImageField(required=False, label='Файл изображения')
        # Убираем из формы поле URL, если оно есть
        if 'product_images_url' in form.base_fields:
            form.base_fields.pop('product_images_url')
        return formset
    
    def image_preview(self, obj):
        """Превью изображения"""
        if obj and obj.product_images_url:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px; object-fit: cover; border-radius: 4px;" />',
                obj.product_images_url
            )
        return "—"
    image_preview.short_description = 'Превью'


class ProductCharacteristicInline(admin.TabularInline):
    """Встроенная форма для характеристик товара"""
    model = Productcharacteristics
    extra = 1
    fields = ('product_characteristics_key', 'product_characteristics_value')


@admin.register(Products)
class ProductAdmin(admin.ModelAdmin):
    """Административная панель для товаров"""
    list_display = (
        "products_id", 
        "products_name", 
        "products_category", 
        "products_brand", 
        "products_price", 
        "products_stock",
        "stock_status"
    )
    list_filter = ("products_category", "products_brand", "products_stock")
    search_fields = ("products_name", "products_description")
    list_display_links = ("products_id", "products_name")
    list_editable = ("products_price", "products_stock")
    ordering = ("-products_id",)
    inlines = [ProductImageInline, ProductCharacteristicInline]
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('products_name', 'products_description', 'products_category', 'products_brand')
        }),
        ('Цена и наличие', {
            'fields': ('products_price', 'products_stock')
        }),
        ('Даты', {
            'fields': ('products_created_at', 'products_updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ("products_created_at", "products_updated_at")
    
    def save_formset(self, request, form, formset, change):
        """Сохраняем inline с поддержкой загрузки файлов и удалений."""
        from django.core.files.storage import default_storage
        from django.utils.text import get_valid_filename
        import os
        # Сначала удаляем помеченные к удалению объекты
        for obj in formset.deleted_objects:
            obj.delete()
        # Сохраняем/обновляем объекты
        for inline_form in formset.forms:
            if not inline_form.has_changed():
                continue
            obj = inline_form.save(commit=False)
            if isinstance(obj, Productimages):
                uploaded = inline_form.cleaned_data.get('upload_image')
                if uploaded:
                    product_id = form.instance.products_id if form.instance and form.instance.pk else obj.product_images_product_id
                    product_id = product_id or 'new'
                    filename = get_valid_filename(uploaded.name)
                    subdir = os.path.join('product_images', str(product_id))
                    path = default_storage.save(os.path.join(subdir, filename), uploaded)
                    try:
                        image_url = default_storage.url(path)
                    except Exception:
                        from django.conf import settings
                        image_url = f"{settings.MEDIA_URL}{path}"
                    obj.product_images_url = image_url
            obj.save()
            inline_form.save_m2m()
    
    def stock_status(self, obj):
        """Статус наличия товара"""
        if obj.products_stock > 10:
            return format_html('<span style="color: green; font-weight: bold;">В наличии</span>')
        elif obj.products_stock > 0:
            return format_html('<span style="color: orange; font-weight: bold;">Мало</span>')
        else:
            return format_html('<span style="color: red; font-weight: bold;">Нет в наличии</span>')
    stock_status.short_description = 'Статус наличия'


@admin.register(Productimages)
class ProductImageAdmin(admin.ModelAdmin):
    """Административная панель для изображений товаров"""
    list_display = ("product_images_id", "image_preview", "product_images_product", "product_images_is_main", "product_link")
    list_filter = ("product_images_is_main", "product_images_product__products_category")
    search_fields = ("product_images_product__products_name",)
    list_display_links = ("product_images_id",)
    list_editable = ("product_images_is_main",)
    ordering = ("-product_images_id",)
    
    # Добавляем отдельное поле загрузки файла при редактировании изображения
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        from django import forms
        form.base_fields['upload_image'] = forms.ImageField(required=False, label='Файл изображения')
        # Скрываем поле product_images_url из формы админки
        if 'brands_logo_url' in form.base_fields:
            form.base_fields.pop('brands_logo_url')
        # Перестановка полей
        form.base_fields.move_to_end('upload_image', last=False)
        return form
    
    def save_model(self, request, obj, form, change):
        uploaded = form.cleaned_data.get('upload_image')
        if uploaded:
            from django.core.files.storage import default_storage
            from django.utils.text import get_valid_filename
            import os
            brand_id = obj.brands_id or 'new'
            filename = get_valid_filename(uploaded.name)
            subdir = os.path.join('brand_logos', str(brand_id))
            path = default_storage.save(os.path.join(subdir, filename), uploaded)
            try:
                image_url = default_storage.url(path)
            except Exception:
                from django.conf import settings
                image_url = f"{settings.MEDIA_URL}{path}"
            obj.brands_logo_url = image_url
        super().save_model(request, obj, form, change)
    
    def image_preview(self, obj):
        """Превью изображения"""
        if obj and obj.product_images_url:
            return format_html(
                '<img src="{}" style="max-height: 60px; max-width: 60px; object-fit: cover; border-radius: 4px; border: 1px solid #ddd;" />',
                obj.product_images_url
            )
        return "—"
    image_preview.short_description = 'Изображение'
    
    def product_link(self, obj):
        """Ссылка на товар"""
        if obj and obj.product_images_product:
            url = reverse('admin:catalog_products_change', args=[obj.product_images_product.products_id])
            return format_html('<a href="{}">{}</a>', url, obj.product_images_product.products_name)
        return "—"
    product_link.short_description = 'Товар'


@admin.register(Productcharacteristics)
class ProductCharacteristicAdmin(admin.ModelAdmin):
    """Административная панель для характеристик товаров"""
    list_display = ("product_characteristics_id", "product_characteristics_product", "product_characteristics_key", "product_characteristics_value")
    list_filter = ("product_characteristics_product__products_category",)
    search_fields = ("product_characteristics_key", "product_characteristics_value", "product_characteristics_product__products_name")
    list_display_links = ("product_characteristics_id", "product_characteristics_product")
    ordering = ("product_characteristics_product", "product_characteristics_key")
