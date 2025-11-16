# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from Apps.orders.models import Orders

class Paymentmethods(models.Model):
    payment_methods_id = models.AutoField(primary_key=True)
    payment_methods_name = models.CharField(unique=True, max_length=100)

    class Meta:
        managed = False
        db_table = 'paymentmethods'
    
    def get_display_name(self):
        """Возвращает переведенное название способа оплаты"""
        # Проверяем, содержит ли название кириллицу (уже на русском)
        if any('\u0400' <= char <= '\u04FF' for char in self.payment_methods_name):
            return self.payment_methods_name
        
        # Словарь переводов для английских названий
        translations = {
            'cash': 'Наличными',
            'card': 'Банковской картой',
            'credit_card': 'Банковской картой',
            'online': 'Онлайн оплата',
            'online_payment': 'Онлайн оплата',
            'bank_transfer': 'Банковский перевод',
            'credit': 'В кредит',
            'installment': 'Рассрочка',
            'payment': 'Оплата',
        }
        name_lower = self.payment_methods_name.lower().strip()
        return translations.get(name_lower, self.payment_methods_name)
    
    def __str__(self):
        return self.get_display_name()
# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.


class Deliverymethods(models.Model):
    delivery_methods_id = models.AutoField(primary_key=True)
    delivery_methods_name = models.CharField(unique=True, max_length=100)
    delivery_methods_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    delivery_methods_description = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'deliverymethods'
    
    def get_display_name(self):
        """Возвращает переведенное название способа доставки"""
        # Проверяем, содержит ли название кириллицу (уже на русском)
        if any('\u0400' <= char <= '\u04FF' for char in self.delivery_methods_name):
            return self.delivery_methods_name
        
        # Словарь переводов для английских названий
        translations = {
            'courier': 'Курьерская доставка',
            'courier_delivery': 'Курьерская доставка',
            'pickup': 'Самовывоз',
            'self_pickup': 'Самовывоз из магазина',
            'post': 'Почтовая доставка',
            'postal': 'Почтовая доставка',
            'express': 'Экспресс-доставка',
            'express_delivery': 'Экспресс-доставка',
            'standard': 'Стандартная доставка',
            'standard_delivery': 'Стандартная доставка',
            'delivery': 'Доставка',
            'shipping': 'Доставка',
        }
        name_lower = self.delivery_methods_name.lower().strip()
        return translations.get(name_lower, self.delivery_methods_name)
    
    def __str__(self):
        display_name = self.get_display_name()
        if self.delivery_methods_cost and float(self.delivery_methods_cost) > 0:
            cost_str = f" ({float(self.delivery_methods_cost):.2f} ₽)"
        else:
            cost_str = " (Бесплатно)"
        return f"{display_name}{cost_str}"
# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.


class Payments(models.Model):
    payments_id = models.AutoField(primary_key=True)
    payments_order = models.ForeignKey(Orders, models.DO_NOTHING)
    payments_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payments_date = models.DateTimeField(blank=True, null=True)
    payments_status = models.CharField(max_length=50)
    payments_transaction_id = models.CharField(unique=True, max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'payments'
