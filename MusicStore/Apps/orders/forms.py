import re
from django import forms
from django.core.exceptions import ValidationError
from Apps.payments.models import Paymentmethods, Deliverymethods


class OrderForm(forms.Form):
    """Форма оформления заказа по ГОСТУ"""
    
    # Новый адрес (если не используется существующий)
    street = forms.CharField(
        max_length=255,
        required=True,
        label='Улица, дом, квартира',
        help_text='Например: ул. Ленина, д. 10, кв. 25'
    )
    
    city = forms.CharField(
        max_length=100,
        required=True,
        label='Город',
        help_text='Например: Москва'
    )
    
    zip_code = forms.CharField(
        max_length=20,
        required=True,
        label='Почтовый индекс',
        help_text='Формат: 6 цифр. Например: 123456'
    )
    
    country = forms.CharField(
        max_length=100,
        required=True,
        label='Страна',
        initial='Россия',
        help_text='Например: Россия'
    )
    
    # Способ доставки (исключаем самовывоз)
    delivery_method = forms.ModelChoiceField(
        queryset=Deliverymethods.objects.exclude(
            delivery_methods_name__icontains='самовывоз'
        ).exclude(
            delivery_methods_name__icontains='pickup'
        ).exclude(
            delivery_methods_name__icontains='self_pickup'
        ),
        required=True,
        label='Способ доставки',
        empty_label=None,
        error_messages={
            'required': 'Необходимо выбрать способ доставки'
        }
    )
    
    # Способ оплаты
    payment_method = forms.ModelChoiceField(
        queryset=Paymentmethods.objects.all(),
        required=True,
        label='Способ оплаты',
        empty_label=None,
        error_messages={
            'required': 'Необходимо выбрать способ оплаты'
        }
    )
    
    # Комментарий к заказу
    comment = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        required=False,
        label='Комментарий к заказу',
        help_text='Дополнительная информация для доставки (необязательно)',
        max_length=1000
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Добавляем классы Bootstrap к полям
        for field_name, field in self.fields.items():
            field.widget.attrs.setdefault('class', 'form-control')
            if field.help_text:
                field.widget.attrs.setdefault('placeholder', field.help_text)
    
    def clean_zip_code(self):
        zip_code = self.cleaned_data.get('zip_code', '').strip()
        if zip_code:
            # Проверка формата почтового индекса (6 цифр для России)
            if not re.match(r'^\d{6}$', zip_code):
                raise ValidationError('Почтовый индекс должен содержать 6 цифр.')
        return zip_code
    
    def clean(self):
        cleaned_data = super().clean()
        street = (cleaned_data.get('street') or '').strip()
        city = (cleaned_data.get('city') or '').strip()
        zip_code = (cleaned_data.get('zip_code') or '').strip()
        country = (cleaned_data.get('country') or '').strip()
        
        # Проверяем обязательные поля для нового адреса
        if not street:
            raise ValidationError({
                'street': 'Укажите улицу, дом и квартиру.'
            })
        if len(street) < 5:
            raise ValidationError({
                'street': 'Адрес слишком короткий. Укажите полный адрес.'
            })
        
        if not city:
            raise ValidationError({
                'city': 'Укажите город.'
            })
        
        if not zip_code:
            raise ValidationError({
                'zip_code': 'Укажите почтовый индекс.'
            })
        
        if not country:
            raise ValidationError({
                'country': 'Укажите страну.'
            })
        
        cleaned_data['street'] = street
        cleaned_data['city'] = city
        cleaned_data['zip_code'] = zip_code
        cleaned_data['country'] = country
        
        return cleaned_data

