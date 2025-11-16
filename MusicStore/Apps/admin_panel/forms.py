from django import forms
from Apps.catalog.models import Products, Categories, Brands, Productimages, Productcharacteristics
from Apps.orders.models import Orders, Orderstatuses
from Apps.users.models import Users
from Apps.payments.models import Paymentmethods, Deliverymethods


class ProductForm(forms.ModelForm):
    """Форма для создания и редактирования товара"""
    class Meta:
        model = Products
        fields = [
            'products_name',
            'products_description',
            'products_price',
            'products_stock',
            'products_category',
            'products_brand',
        ]
        widgets = {
            'products_name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'products_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'products_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'required': True}),
            'products_stock': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'required': True}),
            'products_category': forms.Select(attrs={'class': 'form-control', 'required': True}),
            'products_brand': forms.Select(attrs={'class': 'form-control', 'required': True}),
        }
        labels = {
            'products_name': 'Название товара',
            'products_description': 'Описание',
            'products_price': 'Цена (₽)',
            'products_stock': 'Количество на складе',
            'products_category': 'Категория',
            'products_brand': 'Бренд',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['products_category'].queryset = Categories.objects.all()
        self.fields['products_brand'].queryset = Brands.objects.all()


class CategoryForm(forms.ModelForm):
    """Форма для создания и редактирования категории"""
    class Meta:
        model = Categories
        fields = ['categories_name', 'categories_description']
        widgets = {
            'categories_name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'categories_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'categories_name': 'Название категории',
            'categories_description': 'Описание',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Поле родительской категории скрыто в веб-админке по требованию


class BrandForm(forms.ModelForm):
    """Форма для создания и редактирования бренда"""
    image_file = forms.ImageField(required=False, label='Логотип (файл)')
    class Meta:
        model = Brands
        fields = ['brands_name', 'brands_description']
        widgets = {
            'brands_name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'brands_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'brands_name': 'Название бренда',
            'brands_description': 'Описание',
        }
    
    def clean(self):
        cleaned = super().clean()
        # логотип необязателен, но если указан — ок
        return cleaned


class OrderForm(forms.ModelForm):
    """Форма для редактирования заказа"""
    class Meta:
        model = Orders
        fields = ['orders_status', 'orders_comment']
        widgets = {
            'orders_status': forms.Select(attrs={'class': 'form-control', 'required': True}),
            'orders_comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'orders_status': 'Статус заказа',
            'orders_comment': 'Комментарий',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['orders_status'].queryset = Orderstatuses.objects.all()


class ProductImageForm(forms.ModelForm):
    """Форма для добавления изображения товара"""
    image_file = forms.ImageField(required=False, label='Файл изображения')

    class Meta:
        model = Productimages
        fields = ['product_images_is_main']
        widgets = {
            'product_images_is_main': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'product_images_is_main': 'Главное изображение',
        }
    
    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('image_file'):
            self.add_error('image_file', 'Загрузите файл изображения.')
        return cleaned


class ProductCharacteristicForm(forms.ModelForm):
    """Форма для добавления характеристики товара"""
    class Meta:
        model = Productcharacteristics
        fields = ['product_characteristics_key', 'product_characteristics_value']
        widgets = {
            'product_characteristics_key': forms.TextInput(attrs={'class': 'form-control', 'required': True, 'placeholder': 'Например: Материал'}),
            'product_characteristics_value': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'required': True, 'placeholder': 'Например: Дерево'}),
        }
        labels = {
            'product_characteristics_key': 'Название характеристики',
            'product_characteristics_value': 'Значение',
        }

