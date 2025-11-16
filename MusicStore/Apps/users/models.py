# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Roles(models.Model):
    roles_id = models.AutoField(primary_key=True)
    roles_name = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = False
        db_table = 'roles'
# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.


class Users(models.Model):
    users_id = models.AutoField(primary_key=True)
    users_email = models.CharField(unique=True, max_length=255)
    users_password_hash = models.CharField(max_length=255)
    users_first_name = models.CharField(max_length=100)
    users_last_name = models.CharField(max_length=100)
    users_middle_name = models.CharField(max_length=100, blank=True, null=True)
    users_phone = models.CharField(max_length=20, blank=True, null=True)
    users_secret_word = models.CharField(max_length=255, blank=True, null=True)
    users_created_at = models.DateTimeField(blank=True, null=True)
    users_updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'users'
# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.


class Userroles(models.Model):
    user_roles_id = models.AutoField(primary_key=True)
    user_roles_user = models.ForeignKey(Users, models.DO_NOTHING)
    user_roles_role = models.ForeignKey(Roles, models.DO_NOTHING)
    user_roles_assigned_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'userroles'
        unique_together = (('user_roles_user', 'user_roles_role'),)
# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.


class Addresses(models.Model):
    addresses_id = models.AutoField(primary_key=True)
    addresses_user = models.ForeignKey(Users, models.DO_NOTHING)
    addresses_street = models.CharField(max_length=255)
    addresses_city = models.CharField(max_length=100)
    addresses_zip_code = models.CharField(max_length=20)
    addresses_country = models.CharField(max_length=100, blank=True, null=True)
    addresses_is_default = models.BooleanField(blank=True, null=True)
    addresses_created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'addresses'

    def __str__(self):
        parts = []
        if self.addresses_city:
            parts.append(self.addresses_city)
        if self.addresses_street:
            parts.append(self.addresses_street)
        if self.addresses_zip_code:
            parts.append(self.addresses_zip_code)
        if self.addresses_country:
            parts.append(self.addresses_country)
        return ', '.join(parts) or f'Адрес #{self.addresses_id}'


class Favorites(models.Model):
    favorites_id = models.AutoField(primary_key=True)
    favorites_user = models.ForeignKey(Users, models.DO_NOTHING)
    favorites_product = models.ForeignKey('catalog.Products', models.DO_NOTHING)
    favorites_added_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'favorites'
        unique_together = (('favorites_user', 'favorites_product'),)

    def __str__(self):
        user_name = getattr(self.favorites_user, 'users_email', self.favorites_user_id)
        product_name = getattr(self.favorites_product, 'products_name', self.favorites_product_id)
        return f'Избранное: {user_name} -> {product_name}'


class Usercards(models.Model):
    """Модель для хранения данных банковских карт пользователей"""
    usercards_id = models.AutoField(primary_key=True)
    usercards_user = models.ForeignKey(Users, models.DO_NOTHING)
    # Зашифрованные данные карты
    usercards_card_number_hash = models.CharField(max_length=255)  # Хэш номера карты (последние 4 цифры в открытом виде)
    usercards_card_last_four = models.CharField(max_length=4)  # Последние 4 цифры для отображения
    usercards_card_expiry_encrypted = models.CharField(max_length=255)  # Зашифрованный срок действия
    usercards_card_cvv_hash = models.CharField(max_length=255)  # Хэш CVV (не храним в открытом виде)
    usercards_card_holder_name = models.CharField(max_length=100)  # Имя держателя
    usercards_created_at = models.DateTimeField(blank=True, null=True)
    usercards_updated_at = models.DateTimeField(blank=True, null=True)
    usercards_is_default = models.BooleanField(default=False)

    class Meta:
        managed = False
        db_table = 'usercards'
        
    def __str__(self):
        return f'Карта ****{self.usercards_card_last_four}'