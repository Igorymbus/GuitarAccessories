# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Categories(models.Model):
    categories_id = models.AutoField(primary_key=True)
    categories_name = models.CharField(unique=True, max_length=100)
    categories_parent = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True)
    categories_description = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'categories'

    def __str__(self):
        return self.categories_name
# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Brands(models.Model):
    brands_id = models.AutoField(primary_key=True)
    brands_name = models.CharField(unique=True, max_length=100)
    brands_description = models.TextField(blank=True, null=True)
    brands_logo_url = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'brands'

    def __str__(self):
        return self.brands_name
# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.


class Products(models.Model):
    products_id = models.AutoField(primary_key=True)
    products_name = models.CharField(max_length=255)
    products_description = models.TextField(blank=True, null=True)
    products_price = models.DecimalField(max_digits=10, decimal_places=2)
    products_stock = models.IntegerField()
    products_category = models.ForeignKey(Categories, models.DO_NOTHING)
    products_brand = models.ForeignKey(Brands, models.DO_NOTHING)
    products_created_at = models.DateTimeField(blank=True, null=True)
    products_updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'products'
# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.


class Productimages(models.Model):
    product_images_id = models.AutoField(primary_key=True)
    product_images_product = models.ForeignKey(Products, models.DO_NOTHING)
    product_images_url = models.CharField(max_length=255)
    product_images_is_main = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'productimages'
# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.

class Productcharacteristics(models.Model):
    product_characteristics_id = models.AutoField(primary_key=True)
    product_characteristics_product = models.ForeignKey(Products, models.DO_NOTHING)
    product_characteristics_key = models.CharField(max_length=100)
    product_characteristics_value = models.TextField()

    class Meta:
        managed = False
        db_table = 'productcharacteristics'
        unique_together = (('product_characteristics_product', 'product_characteristics_key'),)
