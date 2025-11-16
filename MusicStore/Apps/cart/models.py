# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from Apps.users.models import Users
from Apps.catalog.models import Products

class Carts(models.Model):
    carts_id = models.AutoField(primary_key=True)
    carts_user = models.ForeignKey(Users, models.DO_NOTHING)
    carts_created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'carts'
# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.


class Cartitems(models.Model):
    cart_items_id = models.AutoField(primary_key=True)
    cart_items_cart = models.ForeignKey(Carts, models.DO_NOTHING)
    cart_items_product = models.ForeignKey(Products, models.DO_NOTHING)
    cart_items_quantity = models.IntegerField()
    cart_items_added_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cartitems'
        unique_together = (('cart_items_cart', 'cart_items_product'),)
