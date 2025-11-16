from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.utils import ProgrammingError
from django.shortcuts import render, redirect, get_object_or_404
from django.db import connection
from django.utils import timezone

from .models import Products, Categories, Brands, Productimages, Productcharacteristics
from .forms import ReviewForm
from Apps.users.models import Users, Favorites
from Apps.extras.models import Reviews
from Apps.users.utils import (
    ensure_favorites_table,
    get_user_favorite_ids,
    register_favorite,
    remove_favorite,
)

_ALLOWED_FAVORITE_REDIRECTS = {'catalog', 'home', 'favorites'}


def _redirect_after_favorite_action(request, default='catalog'):
    target = request.GET.get('next')
    if target in _ALLOWED_FAVORITE_REDIRECTS:
        return redirect(target)
    return redirect(default)


def get_category_and_children_ids(category_id):
    """
    Получает ID выбранной категории и всех её дочерних категорий (рекурсивно).
    Это позволяет показывать товары из родительской категории и всех подкатегорий.
    
    Args:
        category_id: ID категории
        
    Returns:
        list: Список ID категории и всех её дочерних категорий
    """
    category_ids = [category_id]
    
    # Проверяем, существует ли категория
    try:
        category = Categories.objects.get(categories_id=category_id)
    except Categories.DoesNotExist:
        return [category_id]  # Возвращаем только выбранный ID, если категория не существует
    
    # Получаем все дочерние категории первого уровня
    children = Categories.objects.filter(categories_parent_id=category_id)
    
    # Рекурсивно получаем дочерние категории всех уровней
    for child in children:
        category_ids.extend(get_category_and_children_ids(child.categories_id))
    
    return list(set(category_ids))  # Убираем дубликаты


def catalog_view(request):
    """Страница каталога товаров"""
    # Получаем все категории и бренды
    categories = Categories.objects.all()
    brands = Brands.objects.all()
    
    # Начинаем с базового queryset
    products = Products.objects.all()
    
    # Фильтрация по категории, если указана (с учетом иерархии)
    category_id = request.GET.get('category', '').strip()
    if category_id:
        try:
            category_id_int = int(category_id)
            # Получаем ID выбранной категории и всех её дочерних категорий
            category_ids = get_category_and_children_ids(category_id_int)
            # Фильтруем товары по всем найденным категориям
            products = products.filter(products_category_id__in=category_ids)
        except (ValueError, TypeError):
            category_id = ''
    
    # Фильтрация по бренду, если указан
    brand_id = request.GET.get('brand', '').strip()
    if brand_id:
        try:
            brand_id_int = int(brand_id)
            products = products.filter(products_brand_id=brand_id_int)
        except (ValueError, TypeError):
            brand_id = ''
    
    # Поиск по названию, если указан
    search_query = request.GET.get('search', '').strip()
    if search_query:
        products = products.filter(products_name__icontains=search_query)
    
    # Сортировка товаров
    sort_by = request.GET.get('sort', 'default').strip()
    # Валидация параметра сортировки
    valid_sorts = ['default', 'price_asc', 'price_desc', 'name_asc', 'name_desc', 
                   'newest', 'oldest', 'stock_desc', 'stock_asc']
    if sort_by not in valid_sorts:
        sort_by = 'default'
    
    # Опции сортировки
    sort_options = {
        'price_asc': ['products_price', 'products_name'],  # По цене: от дешевых к дорогим, затем по названию
        'price_desc': ['-products_price', 'products_name'],  # По цене: от дорогих к дешевым, затем по названию
        'name_asc': 'products_name',  # По названию: А-Я
        'name_desc': '-products_name',  # По названию: Я-А
        'newest': ['-products_created_at', 'products_id'],  # По дате: новые сначала (NULL в конце)
        'oldest': ['products_created_at', 'products_id'],  # По дате: старые сначала (NULL в конце)
        'stock_desc': ['-products_stock', 'products_name'],  # По наличию: больше на складе
        'stock_asc': ['products_stock', 'products_name'],  # По наличию: меньше на складе
        'default': 'products_id',  # По умолчанию: по ID
    }
    
    # Применяем сортировку
    order_by = sort_options.get(sort_by, 'products_id')
    if isinstance(order_by, list):
        products = products.order_by(*order_by)
    else:
        products = products.order_by(order_by)
    
    # Подсчитываем количество товаров после применения всех фильтров и сортировки
    products_count = products.count()
    
    # Подтягиваем главные изображения для товаров
    product_ids = list(products.values_list('products_id', flat=True))
    images_by_product = {}
    if product_ids:
        main_images = Productimages.objects.filter(
            product_images_product_id__in=product_ids,
            product_images_is_main=True
        )
        for img in main_images:
            images_by_product[img.product_images_product_id] = img.product_images_url
        # Если для некоторых товаров нет главного — берем первое попавшееся
        missing_ids = [pid for pid in product_ids if pid not in images_by_product]
        if missing_ids:
            any_images = (Productimages.objects
                          .filter(product_images_product_id__in=missing_ids)
                          .order_by('product_images_id'))
            for img in any_images:
                if img.product_images_product_id not in images_by_product:
                    images_by_product[img.product_images_product_id] = img.product_images_url
    favorite_ids = set()
    if request.user.is_authenticated:
        try:
            user_model = Users.objects.get(users_email=request.user.email)
            ensure_favorites_table()
            favorite_ids = get_user_favorite_ids(user_model, product_ids)
        except Users.DoesNotExist:
            favorite_ids = set()
        except ProgrammingError:
            favorite_ids = set()
    
    context = {
        'products': products,
        'categories': categories,
        'brands': brands,
        'images_by_product': images_by_product,
        'selected_category': category_id if category_id else '',
        'selected_brand': brand_id if brand_id else '',
        'search_query': search_query if search_query else '',
        'sort_by': sort_by,
        'products_count': products_count,
        'favorite_ids': favorite_ids,
    }
    return render(request, 'catalog/catalog.html', context)


@login_required
def add_to_favorites(request, product_id):
    """Добавляет товар в избранное по ГОСТу (с проверками и уведомлениями)."""
    try:
        user_model = Users.objects.get(users_email=request.user.email)
        product = get_object_or_404(Products, products_id=product_id)
        created = register_favorite(user_model.users_id, product.products_id)
        if created:
            messages.success(request, f'Товар «{product.products_name}» добавлен в избранное.')
        else:
            messages.info(request, f'Товар «{product.products_name}» уже есть в избранном.')
    except Users.DoesNotExist:
        messages.error(request, 'Профиль пользователя не найден.')
    except Exception as exc:
        messages.error(request, f'Не удалось добавить товар в избранное: {exc}')
    return _redirect_after_favorite_action(request)


@login_required
def remove_from_favorites(request, product_id):
    """Удаляет товар из избранного."""
    try:
        user_model = Users.objects.get(users_email=request.user.email)
        product = get_object_or_404(Products, products_id=product_id)
        remove_favorite(user_model.users_id, product.products_id)
        messages.info(request, f'Товар «{product.products_name}» удалён из избранного.')
    except Users.DoesNotExist:
        messages.error(request, 'Профиль пользователя не найден.')
    except Exception as exc:
        messages.error(request, f'Не удалось удалить из избранного: {exc}')
    return _redirect_after_favorite_action(request)


@login_required
def favorites_view(request):
    """Раздел избранных товаров по ГОСТ: карточки, счетчики, визуальные индикаторы."""
    try:
        user_model = Users.objects.get(users_email=request.user.email)
        ensure_favorites_table()
        favorites_qs = (
            Favorites.objects
            .filter(favorites_user=user_model)
            .select_related('favorites_product__products_brand', 'favorites_product__products_category')
            .order_by('-favorites_added_at', '-favorites_id')
        )
        
        favorite_items = []
        product_ids = []
        for fav in favorites_qs:
            try:
                product = fav.favorites_product
            except Products.DoesNotExist:
                continue
            if product:
                favorite_items.append(fav)
                product_ids.append(product.products_id)
        
        images_by_product = {}
        if product_ids:
            main_images = Productimages.objects.filter(
                product_images_product_id__in=product_ids,
                product_images_is_main=True
            )
            for img in main_images:
                images_by_product[img.product_images_product_id] = img.product_images_url
            missing = [pid for pid in product_ids if pid not in images_by_product]
            if missing:
                extra_images = (Productimages.objects
                                .filter(product_images_product_id__in=missing)
                                .order_by('product_images_id'))
                for img in extra_images:
                    images_by_product.setdefault(img.product_images_product_id, img.product_images_url)
        
        favorite_ids = {fav.favorites_product_id for fav in favorite_items}
        
        context = {
            'favorites': favorite_items,
            'images_by_product': images_by_product,
            'favorite_ids': favorite_ids,
            'favorites_count': len(favorite_items),
        }
        return render(request, 'catalog/favorites.html', context)
    except Users.DoesNotExist:
        messages.error(request, 'Профиль пользователя не найден.')
        return redirect('home')
    except Exception as exc:
        messages.error(request, f'Не удалось загрузить избранное: {exc}')
        return redirect('catalog')


def product_detail_view(request, product_id):
    """Детальная страница товара с описанием, характеристиками и отзывами"""
    product = get_object_or_404(Products, products_id=product_id)
    
    # Получаем все изображения товара
    product_images = Productimages.objects.filter(
        product_images_product=product
    ).order_by('-product_images_is_main', 'product_images_id')
    
    # Получаем характеристики товара
    characteristics = Productcharacteristics.objects.filter(
        product_characteristics_product=product
    ).order_by('product_characteristics_key')
    
    # Получаем отзывы (только одобренные)
    reviews = Reviews.objects.filter(
        reviews_product=product,
        reviews_approved=True
    ).select_related('reviews_user').order_by('-reviews_date')
    
    # Вычисляем средний рейтинг
    avg_rating = 0
    if reviews.exists():
        total_rating = sum(review.reviews_rating for review in reviews)
        avg_rating = round(total_rating / reviews.count(), 1)
    
    # Проверяем, в избранном ли товар
    is_favorite = False
    if request.user.is_authenticated:
        try:
            user_model = Users.objects.get(users_email=request.user.email)
            ensure_favorites_table()
            favorite_ids = get_user_favorite_ids(user_model, [product_id])
            is_favorite = product_id in favorite_ids
        except (Users.DoesNotExist, ProgrammingError):
            pass
    
    # Обработка формы отзыва
    review_form = None
    user_review = None
    if request.user.is_authenticated:
        try:
            user_model = Users.objects.get(users_email=request.user.email)
            # Проверяем, есть ли уже отзыв от этого пользователя
            user_review = Reviews.objects.filter(
                reviews_product=product,
                reviews_user=user_model
            ).first()
            
            if request.method == 'POST' and 'review_form' in request.POST:
                if user_review:
                    # Обновляем существующий отзыв
                    review_form = ReviewForm(request.POST, instance=user_review)
                else:
                    # Создаем новый отзыв
                    review_form = ReviewForm(request.POST)
                
                if review_form.is_valid():
                    review = review_form.save(commit=False)
                    review.reviews_product = product
                    review.reviews_user = user_model
                    review.reviews_date = timezone.now()
                    review.reviews_approved = False  # Требует модерации
                    review.save()
                    
                    messages.success(request, 'Ваш отзыв отправлен на модерацию. Спасибо!')
                    return redirect('product_detail', product_id=product_id)
            else:
                if user_review:
                    review_form = ReviewForm(instance=user_review)
                else:
                    review_form = ReviewForm()
        except Users.DoesNotExist:
            pass
    
    context = {
        'product': product,
        'product_images': product_images,
        'characteristics': characteristics,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'reviews_count': reviews.count(),
        'is_favorite': is_favorite,
        'review_form': review_form,
        'user_review': user_review,
    }
    
    return render(request, 'catalog/product_detail.html', context)
