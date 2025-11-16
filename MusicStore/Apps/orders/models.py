# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from Apps.users.models import Users
# Removed circular import: from Apps.payments.models import Paymentmethods, Deliverymethods
from Apps.users.models import Addresses
from Apps.catalog.models import Products


class Orderstatuses(models.Model):
    order_statuses_id = models.AutoField(primary_key=True)
    order_statuses_name = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = False
        db_table = 'orderstatuses'

    def __str__(self):
        return self.order_statuses_name
# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models

class Orders(models.Model):
    orders_id = models.AutoField(primary_key=True)
    orders_user = models.ForeignKey(Users, models.DO_NOTHING)
    orders_total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    orders_date = models.DateTimeField(blank=True, null=True)
    orders_status = models.ForeignKey(Orderstatuses, models.DO_NOTHING)
    orders_payment_method = models.ForeignKey('payments.Paymentmethods', models.DO_NOTHING, blank=True, null=True)
    orders_delivery_method = models.ForeignKey('payments.Deliverymethods', models.DO_NOTHING, blank=True, null=True)
    orders_address = models.ForeignKey(Addresses, models.DO_NOTHING)
    orders_comment = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'orders'
# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Orderitems(models.Model):
    order_items_id = models.AutoField(primary_key=True)
    order_items_order = models.ForeignKey(Orders, models.DO_NOTHING)
    order_items_product = models.ForeignKey(Products, models.DO_NOTHING)
    order_items_quantity = models.IntegerField()
    order_items_price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'orderitems'
# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Orderhistory(models.Model):
    order_history_id = models.AutoField(primary_key=True)
    order_history_order = models.ForeignKey(Orders, models.DO_NOTHING)
    order_history_status = models.ForeignKey(Orderstatuses, models.DO_NOTHING)
    order_history_changed_at = models.DateTimeField(blank=True, null=True)
    order_history_changed_by = models.ForeignKey(Users, models.DO_NOTHING, db_column='order_history_changed_by', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'orderhistory'
