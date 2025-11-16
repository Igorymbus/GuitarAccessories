from rest_framework import viewsets
from .models import Products, Categories, Brands
from .serializers import ProductSerializer, CategorySerializer, BrandSerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Products.objects.all().order_by('-products_id')
    serializer_class = ProductSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Categories.objects.all().order_by('categories_name')
    serializer_class = CategorySerializer


class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brands.objects.all().order_by('brands_name')
    serializer_class = BrandSerializer

from rest_framework import viewsets
from .models import Products, Categories, Brands
from .serializers import ProductSerializer, CategorySerializer, BrandSerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Products.objects.all().order_by('-products_id')
    serializer_class = ProductSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Categories.objects.all().order_by('categories_name')
    serializer_class = CategorySerializer


class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brands.objects.all().order_by('brands_name')
    serializer_class = BrandSerializer



