from rest_framework import serializers
from .models import Products, Categories, Brands


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brands
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):
    categories_parent = serializers.PrimaryKeyRelatedField(
        queryset=Categories.objects.all(), allow_null=True, required=False
    )

    class Meta:
        model = Categories
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    # Writable relations by id
    products_category = serializers.PrimaryKeyRelatedField(queryset=Categories.objects.all())
    products_brand = serializers.PrimaryKeyRelatedField(queryset=Brands.objects.all())
    # Read-only denormalized fields for convenience
    category_name = serializers.CharField(source='products_category.categories_name', read_only=True)
    brand_name = serializers.CharField(source='products_brand.brands_name', read_only=True)

    class Meta:
        model = Products
        fields = [
            'products_id', 'products_name', 'products_description',
            'products_price', 'products_stock',
            'products_category', 'products_brand',
            'category_name', 'brand_name',
            'products_created_at', 'products_updated_at',
        ]

from rest_framework import serializers
from .models import Products, Categories, Brands


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brands
        fields = ['brands_id', 'brands_name', 'brands_description', 'brands_logo_url']


class CategorySerializer(serializers.ModelSerializer):
    parent_id = serializers.IntegerField(source='categories_parent_id', read_only=True)

    class Meta:
        model = Categories
        fields = ['categories_id', 'categories_name', 'categories_description', 'parent_id']


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source='products_category.categories_name', read_only=True)
    brand = serializers.CharField(source='products_brand.brands_name', read_only=True)

    class Meta:
        model = Products
        fields = [
            'products_id', 'products_name', 'products_description',
            'products_price', 'products_stock', 'category', 'brand',
        ]


