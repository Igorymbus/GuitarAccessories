# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from Apps.users.models import Users
from Apps.catalog.models import Products, Categories


class Reviews(models.Model):
    reviews_id = models.AutoField(primary_key=True)
    reviews_product = models.ForeignKey(Products, models.DO_NOTHING)
    reviews_user = models.ForeignKey(Users, models.DO_NOTHING)
    reviews_rating = models.IntegerField()
    reviews_comment = models.TextField(blank=True, null=True)
    reviews_date = models.DateTimeField(blank=True, null=True)
    reviews_approved = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'reviews'
        unique_together = (('reviews_product', 'reviews_user'),)
# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Feedback(models.Model):
    feedback_id = models.AutoField(primary_key=True)
    feedback_user = models.ForeignKey(Users, models.DO_NOTHING, blank=True, null=True)
    feedback_message = models.TextField()
    feedback_date = models.DateTimeField(blank=True, null=True)
    feedback_responded = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'feedback'
# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Analytics(models.Model):
    analytics_id = models.AutoField(primary_key=True)
    analytics_report_type = models.CharField(max_length=50)
    analytics_period_start = models.DateField()
    analytics_period_end = models.DateField()
    analytics_total_orders = models.IntegerField(blank=True, null=True)
    analytics_total_revenue = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    analytics_total_customers = models.IntegerField(blank=True, null=True)
    analytics_avg_order_value = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    analytics_top_product = models.ForeignKey(Products, models.DO_NOTHING, blank=True, null=True)
    analytics_top_category = models.ForeignKey(Categories, models.DO_NOTHING, blank=True, null=True)
    analytics_generated_at = models.DateTimeField(blank=True, null=True)
    analytics_generated_by = models.ForeignKey(Users, models.DO_NOTHING, db_column='analytics_generated_by', blank=True, null=True)
    analytics_data = models.JSONField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'analytics'
        unique_together = (('analytics_report_type', 'analytics_period_start', 'analytics_period_end'),)
