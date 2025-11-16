from django.db.utils import ProgrammingError
from django.shortcuts import render

from Apps.catalog.models import Products, Categories, Brands, Productimages
from Apps.users.models import Users
from Apps.users.utils import ensure_favorites_table, get_user_favorite_ids


def home(request):
    """Главная страница музыкального магазина"""
    # Получаем последние продукты
    latest_products = Products.objects.all()[:8] if Products.objects.exists() else []
    
    # Получаем популярные категории (исключая раздел "Струны")
    categories = (Categories.objects.exclude(categories_name='Струны')[:6]
                  if Categories.objects.exists() else [])
    
    # Получаем популярные бренды
    brands = Brands.objects.all()[:6] if Brands.objects.exists() else []
    
    # Карта товар -> URL изображения (главное, иначе первое)
    images_by_product = {}
    if latest_products:
        product_ids = [p.products_id for p in latest_products]
        main_images = Productimages.objects.filter(
            product_images_product_id__in=product_ids,
            product_images_is_main=True
        )
        for img in main_images:
            images_by_product[img.product_images_product_id] = img.product_images_url
        if len(images_by_product) < len(product_ids):
            other_images = Productimages.objects.filter(
                product_images_product_id__in=product_ids
            ).order_by('product_images_id')
            for img in other_images:
                images_by_product.setdefault(img.product_images_product_id, img.product_images_url)
    
    # Карта категория -> URL изображения (берём главное изображение первого товара категории)
    images_by_category = {}
    if categories:
        category_ids = [c.categories_id for c in categories]
        # Находим по одному товару на категорию
        products_in_categories = (Products.objects
                                  .filter(products_category_id__in=category_ids)
                                  .order_by('products_category_id', 'products_id'))
        seen = set()
        sample_product_ids = []
        for p in products_in_categories:
            if p.products_category_id not in seen:
                seen.add(p.products_category_id)
                sample_product_ids.append(p.products_id)
        if sample_product_ids:
            main_imgs = Productimages.objects.filter(
                product_images_product_id__in=sample_product_ids,
                product_images_is_main=True
            )
            pid_to_url = {img.product_images_product_id: img.product_images_url for img in main_imgs}
            # Дополняем первыми попавшимися, если нет главных
            if len(pid_to_url) < len(sample_product_ids):
                other_imgs = Productimages.objects.filter(
                    product_images_product_id__in=sample_product_ids
                ).order_by('product_images_id')
                for img in other_imgs:
                    pid_to_url.setdefault(img.product_images_product_id, img.product_images_url)
            # Маппим категорию -> url
            for p in products_in_categories:
                if p.products_category_id in seen:
                    url = pid_to_url.get(p.products_id)
                    if url:
                        images_by_category.setdefault(p.products_category_id, url)
    
    favorite_ids = set()
    if request.user.is_authenticated and latest_products:
        try:
            user_model = Users.objects.get(users_email=request.user.email)
            ensure_favorites_table()
            favorite_ids = get_user_favorite_ids(user_model, [p.products_id for p in latest_products])
        except Users.DoesNotExist:
            favorite_ids = set()
        except ProgrammingError:
            favorite_ids = set()
    
    context = {
        'latest_products': latest_products,
        'categories': categories,
        'brands': brands,
        'images_by_product': images_by_product,
        'images_by_category': images_by_category,
        'favorite_ids': favorite_ids,
    }
    return render(request, 'main/home.html', context)
