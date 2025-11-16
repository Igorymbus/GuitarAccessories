from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import connection, transaction
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.db.models import Sum, Count, Avg, Q
from datetime import datetime, timedelta
from decimal import Decimal
import json
from .decorators import admin_required
from .forms import ProductForm, CategoryForm, BrandForm, OrderForm, ProductImageForm, ProductCharacteristicForm
from Apps.catalog.models import Products, Categories, Brands, Productimages, Productcharacteristics
from Apps.orders.models import Orders, Orderitems, Orderstatuses, Orderhistory
from Apps.users.models import Users
from Apps.payments.models import Paymentmethods, Deliverymethods
from Apps.cart.models import Carts, Cartitems
from Apps.extras.models import Reviews


@admin_required
def admin_dashboard(request):
    """Главная страница админ-панели"""
    # Статистика
    stats = {
        'total_products': Products.objects.count(),
        'total_orders': Orders.objects.count(),
        'total_users': Users.objects.count(),
        'total_categories': Categories.objects.count(),
        'total_brands': Brands.objects.count(),
        'pending_orders': Orders.objects.filter(orders_status__order_statuses_name='Новый').count() if Orderstatuses.objects.filter(order_statuses_name='Новый').exists() else 0,
    }
    
    # Последние заказы
    recent_orders = Orders.objects.order_by('-orders_date')[:10]
    
    # Товары с низким остатком
    low_stock_products = Products.objects.filter(products_stock__lte=10).order_by('products_stock')[:10]
    
    context = {
        'stats': stats,
        'recent_orders': recent_orders,
        'low_stock_products': low_stock_products,
    }
    return render(request, 'admin_panel/dashboard.html', context)


# ============ УПРАВЛЕНИЕ ТОВАРАМИ ============

@admin_required
def admin_products(request):
    """Список товаров"""
    products = Products.objects.select_related('products_category', 'products_brand').all().order_by('-products_id')
    
    # Поиск
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(products_name__icontains=search_query)
    
    # Фильтр по категории
    category_filter = request.GET.get('category', '')
    if category_filter:
        products = products.filter(products_category_id=category_filter)
    
    # Фильтр по бренду
    brand_filter = request.GET.get('brand', '')
    if brand_filter:
        products = products.filter(products_brand_id=brand_filter)
    
    # Пагинация
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = Categories.objects.all()
    brands = Brands.objects.all()
    
    context = {
        'products': page_obj,
        'categories': categories,
        'brands': brands,
        'search_query': search_query,
        'category_filter': category_filter,
        'brand_filter': brand_filter,
    }
    return render(request, 'admin_panel/products/list.html', context)


@admin_required
def admin_product_create(request):
    """Создание товара"""
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            # Используем raw SQL для создания товара (так как managed=False)
            product = form.save(commit=False)
            with connection.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO products (products_name, products_description, products_price, products_stock, 
                       products_category_id, products_brand_id, products_created_at, products_updated_at)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                       RETURNING products_id""",
                    [
                        product.products_name,
                        product.products_description or '',
                        product.products_price,
                        product.products_stock,
                        product.products_category.categories_id,
                        product.products_brand.brands_id,
                        timezone.now(),
                        timezone.now(),
                    ]
                )
                product_id = cursor.fetchone()[0]
            messages.success(request, f'Товар "{product.products_name}" успешно создан!')
            return redirect('admin_product_edit', product_id=product_id)
    else:
        form = ProductForm()
    
    return render(request, 'admin_panel/products/form.html', {'form': form, 'action': 'Создать'})


@admin_required
def admin_product_edit(request, product_id):
    """Редактирование товара"""
    product = get_object_or_404(Products, pk=product_id)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            # Используем raw SQL для обновления товара
            with connection.cursor() as cursor:
                cursor.execute(
                    """UPDATE products 
                       SET products_name = %s, products_description = %s, products_price = %s, 
                           products_stock = %s, products_category_id = %s, products_brand_id = %s, 
                           products_updated_at = %s
                       WHERE products_id = %s""",
                    [
                        form.cleaned_data['products_name'],
                        form.cleaned_data['products_description'] or '',
                        form.cleaned_data['products_price'],
                        form.cleaned_data['products_stock'],
                        form.cleaned_data['products_category'].categories_id,
                        form.cleaned_data['products_brand'].brands_id,
                        timezone.now(),
                        product_id,
                    ]
                )
            messages.success(request, f'Товар "{product.products_name}" успешно обновлен!')
            return redirect('admin_product_edit', product_id=product_id)
    else:
        form = ProductForm(instance=product)
    
    # Изображения товара
    images = Productimages.objects.filter(product_images_product=product)
    
    # Характеристики товара
    characteristics = Productcharacteristics.objects.filter(product_characteristics_product=product)
    
    context = {
        'form': form,
        'product': product,
        'images': images,
        'characteristics': characteristics,
        'action': 'Редактировать',
    }
    return render(request, 'admin_panel/products/form.html', context)


@admin_required
def admin_product_delete(request, product_id):
    """Удаление товара"""
    product = get_object_or_404(Products, pk=product_id)
    
    if request.method == 'POST':
        product_name = product.products_name
        # Используем raw SQL для удаления товара
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM products WHERE products_id = %s", [product_id])
        messages.success(request, f'Товар "{product_name}" успешно удален!')
        return redirect('admin_products')
    
    return render(request, 'admin_panel/products/delete.html', {'product': product})


@admin_required
def admin_product_add_image(request, product_id):
    """Добавление изображения товара"""
    product = get_object_or_404(Products, pk=product_id)
    
    if request.method == 'POST':
        form = ProductImageForm(request.POST, request.FILES)
        if form.is_valid():
            # Если загружен файл — сохраняем его и подставляем URL в поле
            uploaded = form.cleaned_data.get('image_file')
            image_url = ''
            if uploaded:
                from django.core.files.storage import default_storage
                from django.utils.text import get_valid_filename
                import os
                filename = get_valid_filename(uploaded.name)
                subdir = os.path.join('product_images', str(product_id))
                path = default_storage.save(os.path.join(subdir, filename), uploaded)
                # Получаем URL к файлу
                try:
                    from django.core.files.storage import FileSystemStorage
                    # Для FileSystemStorage storage.url даст MEDIA_URL + path
                    image_url = default_storage.url(path)
                except Exception:
                    # Фоллбек на относительный путь
                    from django.conf import settings
                    image_url = f"{settings.MEDIA_URL}{path}"

            # Если это главное изображение, снимаем флаг с других
            if form.cleaned_data['product_images_is_main']:
                Productimages.objects.filter(
                    product_images_product=product,
                    product_images_is_main=True
                ).update(product_images_is_main=False)
            
            # Используем raw SQL для создания изображения
            with connection.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO productimages (product_images_product_id, product_images_url, product_images_is_main)
                       VALUES (%s, %s, %s)
                       RETURNING product_images_id""",
                    [
                        product_id,
                        image_url,
                        form.cleaned_data['product_images_is_main'] or False,
                    ]
                )
            messages.success(request, 'Изображение успешно добавлено!')
            return redirect('admin_product_edit', product_id=product_id)
    else:
        form = ProductImageForm()
    
    return render(request, 'admin_panel/products/add_image.html', {'form': form, 'product': product})


@admin_required
def admin_product_add_characteristic(request, product_id):
    """Добавление характеристики товара"""
    product = get_object_or_404(Products, pk=product_id)
    
    if request.method == 'POST':
        form = ProductCharacteristicForm(request.POST)
        if form.is_valid():
            # Используем raw SQL для создания характеристики
            with connection.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO productcharacteristics (product_characteristics_product_id, product_characteristics_key, product_characteristics_value)
                       VALUES (%s, %s, %s)
                       RETURNING product_characteristics_id""",
                    [
                        product_id,
                        form.cleaned_data['product_characteristics_key'],
                        form.cleaned_data['product_characteristics_value'],
                    ]
                )
            messages.success(request, 'Характеристика успешно добавлена!')
            return redirect('admin_product_edit', product_id=product_id)
    else:
        form = ProductCharacteristicForm()
    
    return render(request, 'admin_panel/products/add_characteristic.html', {'form': form, 'product': product})


# ============ УПРАВЛЕНИЕ КАТЕГОРИЯМИ ============

@admin_required
def admin_categories(request):
    """Список категорий"""
    categories = Categories.objects.select_related('categories_parent')\
        .exclude(categories_name='Струны для гитар')\
        .order_by('categories_name')
    return render(request, 'admin_panel/categories/list.html', {'categories': categories})


@admin_required
def admin_category_create(request):
    """Создание категории"""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            with connection.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO categories (categories_name, categories_parent_id, categories_description)
                       VALUES (%s, %s, %s)
                       RETURNING categories_id""",
                    [
                        cleaned_data['categories_name'],
                        None,
                        cleaned_data['categories_description'] or '',
                    ]
                )
                category_id = cursor.fetchone()[0]
            messages.success(request, f'Категория "{cleaned_data["categories_name"]}" успешно создана!')
            return redirect('admin_categories')
    else:
        form = CategoryForm()
    
    return render(request, 'admin_panel/categories/form.html', {'form': form, 'action': 'Создать'})


@admin_required
def admin_category_edit(request, category_id):
    """Редактирование категории"""
    category = get_object_or_404(Categories, pk=category_id)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            with connection.cursor() as cursor:
                cursor.execute(
                    """UPDATE categories 
                       SET categories_name = %s, categories_parent_id = %s, categories_description = %s
                       WHERE categories_id = %s""",
                    [
                        form.cleaned_data['categories_name'],
                        category.categories_parent_id,
                        form.cleaned_data['categories_description'] or '',
                        category_id,
                    ]
                )
            messages.success(request, f'Категория "{category.categories_name}" успешно обновлена!')
            return redirect('admin_categories')
    else:
        form = CategoryForm(instance=category)
    
    return render(request, 'admin_panel/categories/form.html', {'form': form, 'category': category, 'action': 'Редактировать'})


@admin_required
def admin_category_delete(request, category_id):
    """Удаление категории"""
    category = get_object_or_404(Categories, pk=category_id)
    
    if request.method == 'POST':
        category_name = category.categories_name
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM categories WHERE categories_id = %s", [category_id])
        messages.success(request, f'Категория "{category_name}" успешно удалена!')
        return redirect('admin_categories')
    
    return render(request, 'admin_panel/categories/delete.html', {'category': category})


# ============ УПРАВЛЕНИЕ БРЕНДАМИ ============

@admin_required
def admin_brands(request):
    """Список брендов"""
    brands = Brands.objects.all().order_by('brands_name')
    return render(request, 'admin_panel/brands/list.html', {'brands': brands})


@admin_required
def admin_brand_create(request):
    """Создание бренда"""
    if request.method == 'POST':
        form = BrandForm(request.POST, request.FILES)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            # Сохраняем файл логотипа, если задан
            logo_url = ''
            uploaded = cleaned_data.get('image_file')
            if uploaded:
                from django.core.files.storage import default_storage
                from django.utils.text import get_valid_filename
                import os
                filename = get_valid_filename(uploaded.name)
                subdir = os.path.join('brand_logos')
                path = default_storage.save(os.path.join(subdir, filename), uploaded)
                try:
                    logo_url = default_storage.url(path)
                except Exception:
                    from django.conf import settings
                    logo_url = f"{settings.MEDIA_URL}{path}"
            with connection.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO brands (brands_name, brands_description, brands_logo_url)
                       VALUES (%s, %s, %s)
                       RETURNING brands_id""",
                    [
                        cleaned_data['brands_name'],
                        cleaned_data['brands_description'] or '',
                        logo_url or '',
                    ]
                )
                brand_id = cursor.fetchone()[0]
            messages.success(request, f'Бренд "{cleaned_data["brands_name"]}" успешно создан!')
            return redirect('admin_brands')
    else:
        form = BrandForm()
    
    return render(request, 'admin_panel/brands/form.html', {'form': form, 'action': 'Создать'})


@admin_required
def admin_brand_edit(request, brand_id):
    """Редактирование бренда"""
    brand = get_object_or_404(Brands, pk=brand_id)
    
    if request.method == 'POST':
        form = BrandForm(request.POST, request.FILES, instance=brand)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            logo_url = brand.brands_logo_url or ''
            uploaded = cleaned_data.get('image_file')
            if uploaded:
                from django.core.files.storage import default_storage
                from django.utils.text import get_valid_filename
                import os
                filename = get_valid_filename(uploaded.name)
                subdir = os.path.join('brand_logos', str(brand_id))
                path = default_storage.save(os.path.join(subdir, filename), uploaded)
                try:
                    logo_url = default_storage.url(path)
                except Exception:
                    from django.conf import settings
                    logo_url = f"{settings.MEDIA_URL}{path}"
            with connection.cursor() as cursor:
                cursor.execute(
                    """UPDATE brands 
                       SET brands_name = %s, brands_description = %s, brands_logo_url = %s
                       WHERE brands_id = %s""",
                    [
                        cleaned_data['brands_name'],
                        cleaned_data['brands_description'] or '',
                        logo_url or '',
                        brand_id,
                    ]
                )
            messages.success(request, f'Бренд "{brand.brands_name}" успешно обновлен!')
            return redirect('admin_brands')
    else:
        form = BrandForm(instance=brand)
    
    return render(request, 'admin_panel/brands/form.html', {'form': form, 'brand': brand, 'action': 'Редактировать'})


@admin_required
def admin_brand_delete(request, brand_id):
    """Удаление бренда"""
    brand = get_object_or_404(Brands, pk=brand_id)
    
    if request.method == 'POST':
        brand_name = brand.brands_name
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM brands WHERE brands_id = %s", [brand_id])
        messages.success(request, f'Бренд "{brand_name}" успешно удален!')
        return redirect('admin_brands')
    
    return render(request, 'admin_panel/brands/delete.html', {'brand': brand})


# ============ УПРАВЛЕНИЕ ЗАКАЗАМИ ============

@admin_required
def admin_orders(request):
    """Список заказов"""
    orders = Orders.objects.select_related(
        'orders_user', 'orders_status', 'orders_payment_method', 'orders_delivery_method'
    ).all().order_by('-orders_date')
    
    # Фильтр по статусу
    status_filter = request.GET.get('status', '')
    if status_filter:
        orders = orders.filter(orders_status_id=status_filter)
    
    # Поиск
    search_query = request.GET.get('search', '')
    if search_query:
        orders = orders.filter(
            orders_id__icontains=search_query
        ) | orders.filter(
            orders_user__users_email__icontains=search_query
        )
    
    # Пагинация
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    statuses = Orderstatuses.objects.all()
    
    context = {
        'orders': page_obj,
        'statuses': statuses,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    return render(request, 'admin_panel/orders/list.html', context)


@admin_required
def admin_order_detail(request, order_id):
    """Детали заказа"""
    order = get_object_or_404(Orders, pk=order_id)
    order_items = Orderitems.objects.filter(order_items_order=order).select_related('order_items_product')
    
    # Проверяем, отменен ли заказ (для блокировки формы)
    # Нормализуем строку: заменяем "ё" на "е" для корректной проверки
    order_status_name = order.orders_status.order_statuses_name.lower().replace('ё', 'е')
    is_cancelled_order = 'отмен' in order_status_name
    
    if request.method == 'POST':
        # Если заказ уже отменен, блокируем изменения
        if is_cancelled_order:
            messages.error(request, f'Заказ #{order_id} отменен и не может быть изменен!')
            return redirect('admin_order_detail', order_id=order_id)
        
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            new_status = form.cleaned_data['orders_status']
            new_status_name = new_status.order_statuses_name
            new_status_name_lower = new_status_name.lower()
            
            # Проверяем, установлен ли статус на отмененный (проверяем все варианты)
            # Нормализуем строки: заменяем "ё" на "е" для корректной проверки
            new_status_normalized = new_status_name_lower.replace('ё', 'е')
            
            is_cancelled = 'отмен' in new_status_normalized
            
            # Используем транзакцию для атомарности операций
            with transaction.atomic():
                # Обновляем статус заказа
                with connection.cursor() as cursor:
                    cursor.execute(
                        """UPDATE orders 
                           SET orders_status_id = %s, orders_comment = %s
                           WHERE orders_id = %s""",
                        [
                            new_status.order_statuses_id,
                            form.cleaned_data['orders_comment'] or '',
                            order_id,
                        ]
                    )
                
                # Если статус установлен на отмененный, возвращаем товары на склад
                if is_cancelled:
                    print(f"DEBUG: Статус отменен! Возвращаем товары на склад для заказа #{order_id}")
                    # Получаем товары заказа напрямую из БД
                    with connection.cursor() as cursor:
                        cursor.execute(
                            """SELECT oi.order_items_product_id, oi.order_items_quantity, p.products_name
                               FROM orderitems oi
                               JOIN products p ON oi.order_items_product_id = p.products_id
                               WHERE oi.order_items_order_id = %s""",
                            [order_id]
                        )
                        order_items_data = cursor.fetchall()
                    
                    if not order_items_data:
                        messages.warning(
                            request, 
                            f'Заказ #{order_id} отменен, но в заказе нет товаров для возврата на склад.'
                        )
                    else:
                        # Возвращаем товары на склад
                        returned_count = 0
                        failed_count = 0
                        returned_products = []
                        failed_products = []
                        
                        with connection.cursor() as cursor:
                            for product_id, quantity, product_name in order_items_data:
                                try:
                                    # Получаем текущий остаток для проверки
                                    cursor.execute(
                                        "SELECT products_stock FROM products WHERE products_id = %s",
                                        [product_id]
                                    )
                                    result = cursor.fetchone()
                                    old_stock = result[0] if result else 0
                                    
                                    # Увеличиваем остаток товара на складе
                                    cursor.execute(
                                        """UPDATE products 
                                           SET products_stock = products_stock + %s
                                           WHERE products_id = %s""",
                                        [quantity, product_id]
                                    )
                                    
                                    # Проверяем, что обновление прошло успешно
                                    cursor.execute(
                                        "SELECT products_stock FROM products WHERE products_id = %s",
                                        [product_id]
                                    )
                                    result = cursor.fetchone()
                                    new_stock = result[0] if result else old_stock
                                    
                                    if new_stock == old_stock + quantity:
                                        returned_count += 1
                                        returned_products.append(f"{product_name} (+{quantity} шт.)")
                                    else:
                                        failed_count += 1
                                        failed_products.append(f"{product_name} (ожидалось: {old_stock + quantity}, получено: {new_stock})")
                                except Exception as e:
                                    failed_count += 1
                                    failed_products.append(f"{product_name} (ошибка: {str(e)})")
                        
                        if returned_count > 0:
                            msg = f'Заказ #{order_id} отменен. {returned_count} товар(ов) возвращено на склад!'
                            if returned_products:
                                msg += f' Товары: {", ".join(returned_products)}'
                            messages.success(request, msg)
                        
                        if failed_count > 0:
                            msg = f'Не удалось вернуть {failed_count} товар(ов) на склад: {", ".join(failed_products)}'
                            messages.error(request, msg)
                else:
                    # Если статус не отменен, просто обновляем заказ
                    messages.success(request, f'Заказ #{order_id} успешно обновлен!')
            
            return redirect('admin_order_detail', order_id=order_id)
    else:
        form = OrderForm(instance=order)
    
    context = {
        'order': order,
        'order_items': order_items,
        'form': form,
        'is_cancelled_order': is_cancelled_order,
    }
    return render(request, 'admin_panel/orders/detail.html', context)


@admin_required
def admin_order_delete(request, order_id):
    """Удаление заказа"""
    order = get_object_or_404(Orders, pk=order_id)
    
    if request.method == 'POST':
        order_id_val = order.orders_id
        
        # Удаляем связанные записи через raw SQL
        with connection.cursor() as cursor:
            # Сначала удаляем товары заказа (orderitems)
            cursor.execute("DELETE FROM orderitems WHERE order_items_order_id = %s", [order_id_val])
            # Удаляем историю заказа (orderhistory), если она есть
            cursor.execute("DELETE FROM orderhistory WHERE order_history_order_id = %s", [order_id_val])
            # Удаляем сам заказ
            cursor.execute("DELETE FROM orders WHERE orders_id = %s", [order_id_val])
        
        messages.success(request, f'Заказ #{order_id_val} успешно удален!')
        return redirect('admin_orders')
    
    # Подсчитываем количество товаров в заказе
    order_items_count = Orderitems.objects.filter(order_items_order=order).count()
    
    return render(request, 'admin_panel/orders/delete.html', {
        'order': order,
        'order_items_count': order_items_count
    })


# ============ УПРАВЛЕНИЕ ОТЗЫВАМИ ============

@admin_required
def admin_reviews(request):
    """Список отзывов"""
    reviews = Reviews.objects.select_related(
        'reviews_product', 'reviews_user'
    ).all().order_by('-reviews_date')
    
    # Фильтр по статусу одобрения
    approved_filter = request.GET.get('approved', '')
    if approved_filter == 'pending':
        reviews = reviews.filter(reviews_approved__isnull=True)
    elif approved_filter == 'approved':
        reviews = reviews.filter(reviews_approved=True)
    elif approved_filter == 'rejected':
        reviews = reviews.filter(reviews_approved=False)
    
    # Поиск
    search_query = request.GET.get('search', '')
    if search_query:
        reviews = reviews.filter(
            reviews_product__products_name__icontains=search_query
        ) | reviews.filter(
            reviews_user__users_email__icontains=search_query
        ) | reviews.filter(
            reviews_comment__icontains=search_query
        )
    
    # Пагинация
    paginator = Paginator(reviews, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Статистика
    all_reviews = Reviews.objects.all()
    stats = {
        'total': all_reviews.count(),
        'pending': all_reviews.filter(reviews_approved__isnull=True).count(),
        'approved': all_reviews.filter(reviews_approved=True).count(),
        'rejected': all_reviews.filter(reviews_approved=False).count(),
    }
    
    context = {
        'reviews': page_obj,
        'approved_filter': approved_filter,
        'search_query': search_query,
        'stats': stats,
    }
    return render(request, 'admin_panel/reviews/list.html', context)


@admin_required
def admin_review_approve(request, review_id):
    """Одобрение отзыва"""
    review = get_object_or_404(Reviews, pk=review_id)
    
    if request.method == 'POST':
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE reviews SET reviews_approved = TRUE WHERE reviews_id = %s",
                [review_id]
            )
        messages.success(request, f'Отзыв #{review_id} одобрен и опубликован.')
        return redirect('admin_reviews')
    
    context = {
        'review': review,
    }
    return render(request, 'admin_panel/reviews/approve.html', context)


@admin_required
def admin_review_reject(request, review_id):
    """Отклонение отзыва"""
    review = get_object_or_404(Reviews, pk=review_id)
    
    if request.method == 'POST':
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE reviews SET reviews_approved = FALSE WHERE reviews_id = %s",
                [review_id]
            )
        messages.success(request, f'Отзыв #{review_id} отклонен.')
        return redirect('admin_reviews')
    
    context = {
        'review': review,
    }
    return render(request, 'admin_panel/reviews/reject.html', context)


@admin_required
def admin_review_delete(request, review_id):
    """Удаление отзыва"""
    review = get_object_or_404(Reviews, pk=review_id)
    
    if request.method == 'POST':
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM reviews WHERE reviews_id = %s",
                [review_id]
            )
        messages.success(request, f'Отзыв #{review_id} удален.')
        return redirect('admin_reviews')
    
    context = {
        'review': review,
    }
    return render(request, 'admin_panel/reviews/delete.html', context)


# ============ АНАЛИТИКА ============

@admin_required
def admin_analytics(request):
    """Страница аналитики с графиками продаж"""
    # Период для анализа (последние 30 дней по умолчанию)
    days = int(request.GET.get('days', 30))
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # Получаем ID статусов отмененных заказов (исключаем их из аналитики)
    cancelled_status_ids = []
    for status in Orderstatuses.objects.all():
        status_name_normalized = status.order_statuses_name.lower().replace('ё', 'е')
        if 'отмен' in status_name_normalized:
            cancelled_status_ids.append(status.order_statuses_id)
    
    # Базовый фильтр для заказов (исключаем отмененные)
    base_orders_filter = Orders.objects.filter(orders_date__gte=start_date)
    if cancelled_status_ids:
        base_orders_filter = base_orders_filter.exclude(orders_status_id__in=cancelled_status_ids)
    
    # Общая статистика
    total_orders = base_orders_filter.count()
    total_revenue = base_orders_filter.aggregate(total=Sum('orders_total_amount'))['total'] or Decimal('0')
    
    # Статистика по дням
    daily_stats = []
    current_date = start_date.date()
    while current_date <= end_date.date():
        day_orders = Orders.objects.filter(orders_date__date=current_date)
        if cancelled_status_ids:
            day_orders = day_orders.exclude(orders_status_id__in=cancelled_status_ids)
        day_count = day_orders.count()
        day_revenue = day_orders.aggregate(total=Sum('orders_total_amount'))['total'] or Decimal('0')
        
        daily_stats.append({
            'date': current_date.strftime('%d.%m'),
            'orders': day_count,
            'revenue': float(day_revenue)
        })
        current_date += timedelta(days=1)
    
    # Топ товаров по продажам (исключаем отмененные заказы)
    top_products = Orderitems.objects.filter(
        order_items_order__orders_date__gte=start_date
    )
    if cancelled_status_ids:
        top_products = top_products.exclude(order_items_order__orders_status_id__in=cancelled_status_ids)
    top_products = top_products.values(
        'order_items_product__products_name',
        'order_items_product__products_id'
    ).annotate(
        total_quantity=Sum('order_items_quantity'),
        total_revenue=Sum('order_items_price_at_purchase')
    ).order_by('-total_quantity')[:10]
    
    # Статистика по категориям (исключаем отмененные заказы)
    category_stats = Orderitems.objects.filter(
        order_items_order__orders_date__gte=start_date
    )
    if cancelled_status_ids:
        category_stats = category_stats.exclude(order_items_order__orders_status_id__in=cancelled_status_ids)
    category_stats = category_stats.values(
        'order_items_product__products_category__categories_name'
    ).annotate(
        total_quantity=Sum('order_items_quantity'),
        total_revenue=Sum('order_items_price_at_purchase')
    ).order_by('-total_revenue')[:10]
    
    # Статистика по статусам заказов (исключаем отмененные заказы)
    status_stats = base_orders_filter.values(
        'orders_status__order_statuses_name'
    ).annotate(
        count=Count('orders_id')
    )
    
    # Статистика по способам оплаты (исключаем отмененные заказы)
    payment_stats = base_orders_filter.values(
        'orders_payment_method__payment_methods_name'
    ).annotate(
        count=Count('orders_id'),
        revenue=Sum('orders_total_amount')
    )
    
    # Статистика по способам доставки (исключаем отмененные заказы)
    delivery_stats = base_orders_filter.values(
        'orders_delivery_method__delivery_methods_name'
    ).annotate(
        count=Count('orders_id'),
        revenue=Sum('orders_total_amount')
    )
    
    # Средний чек (исключаем отмененные заказы)
    avg_order_value = base_orders_filter.aggregate(avg=Avg('orders_total_amount'))['avg'] or Decimal('0')
    
    # Преобразуем QuerySet в списки и конвертируем Decimal в float для JSON
    def convert_decimal_to_float(obj):
        """Рекурсивно конвертирует Decimal в float"""
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: convert_decimal_to_float(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_decimal_to_float(item) for item in obj]
        return obj
    
    top_products_list = convert_decimal_to_float(list(top_products))
    category_stats_list = convert_decimal_to_float(list(category_stats))
    status_stats_list = convert_decimal_to_float(list(status_stats))
    payment_stats_list = convert_decimal_to_float(list(payment_stats))
    delivery_stats_list = convert_decimal_to_float(list(delivery_stats))
    
    context = {
        'days': days,
        'start_date': start_date.date(),
        'end_date': end_date.date(),
        'total_orders': total_orders,
        'total_revenue': float(total_revenue),
        'avg_order_value': float(avg_order_value),
        'daily_stats': json.dumps(daily_stats),
        'top_products': json.dumps(top_products_list),
        'category_stats': json.dumps(category_stats_list),
        'status_stats': json.dumps(status_stats_list),
        'payment_stats': json.dumps(payment_stats_list),
        'delivery_stats': json.dumps(delivery_stats_list),
    }
    
    return render(request, 'admin_panel/analytics/dashboard.html', context)


@admin_required
def admin_analytics_export_pdf(request):
    """Экспорт аналитики в PDF"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from io import BytesIO
        import os
        import matplotlib
        matplotlib.use('Agg')  # Используем backend без GUI
        import matplotlib.pyplot as plt
        import matplotlib.font_manager as fm
        import numpy as np
        
        # Период для анализа
        days = int(request.GET.get('days', 30))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Настройка matplotlib для поддержки кириллицы
        plt.rcParams['font.family'] = 'DejaVu Sans'
        # Пытаемся использовать шрифт с поддержкой кириллицы
        try:
            import platform
            if platform.system() == 'Windows':
                font_paths = [
                    'C:/Windows/Fonts/arial.ttf',
                    'C:/Windows/Fonts/ARIAL.TTF',
                ]
                for font_path in font_paths:
                    if os.path.exists(font_path):
                        prop = fm.FontProperties(fname=font_path)
                        plt.rcParams['font.family'] = prop.get_name()
                        break
        except:
            pass
        
        # Создаем PDF в памяти
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                               rightMargin=30, leftMargin=30,
                               topMargin=30, bottomMargin=30)
        story = []
        styles = getSampleStyleSheet()
        
        # Регистрируем шрифт с поддержкой кириллицы
        # Пытаемся использовать системные шрифты Windows с поддержкой кириллицы
        font_name = 'Helvetica'
        cyrillic_font_registered = False
        
        # Пытаемся зарегистрировать шрифт с поддержкой кириллицы
        try:
            import platform
            system = platform.system()
            
            # Для Windows используем системные шрифты
            if system == 'Windows':
                # Пытаемся найти Arial или Times New Roman
                font_paths = [
                    'C:/Windows/Fonts/arial.ttf',
                    'C:/Windows/Fonts/ARIAL.TTF',
                    'C:/Windows/Fonts/times.ttf',
                    'C:/Windows/Fonts/TIMES.TTF',
                ]
                
                for font_path in font_paths:
                    try:
                        if os.path.exists(font_path):
                            pdfmetrics.registerFont(TTFont('CyrillicFont', font_path))
                            font_name = 'CyrillicFont'
                            cyrillic_font_registered = True
                            break
                    except:
                        continue
        except Exception as e:
            # Если не удалось зарегистрировать, используем стандартный шрифт
            # Paragraph все равно будет работать с Unicode через правильную обработку
            pass
        
        # Стили с поддержкой кириллицы
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f6feb'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName=font_name
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1f6feb'),
            spaceAfter=12,
            spaceBefore=20,
            fontName=font_name
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            fontName=font_name
        )
        
        # Функция для безопасного создания Paragraph с кириллицей
        def safe_paragraph(text, style):
            """Создает Paragraph с правильной обработкой кириллицы"""
            if not text:
                return Paragraph('', style)
            # Убеждаемся, что текст в правильной кодировке
            if isinstance(text, bytes):
                text = text.decode('utf-8')
            text_str = str(text)
            # Экранируем специальные символы для XML/HTML (Paragraph использует XML)
            text_str = text_str.replace('&', '&amp;')
            text_str = text_str.replace('<', '&lt;')
            text_str = text_str.replace('>', '&gt;')
            return Paragraph(text_str, style)
        
        # Функция для создания простого текста
        def safe_text(text):
            """Создает безопасный текст"""
            if not text:
                return ''
            if isinstance(text, bytes):
                text = text.decode('utf-8')
            return str(text)
        
        # Заголовок
        story.append(safe_paragraph("Отчет по аналитике продаж", title_style))
        story.append(safe_paragraph(
            f"Период: {start_date.date().strftime('%d.%m.%Y')} - {end_date.date().strftime('%d.%m.%Y')}",
            normal_style
        ))
        story.append(Spacer(1, 0.3*inch))
        
        # Получаем ID статусов отмененных заказов (исключаем их из аналитики)
        cancelled_status_ids = []
        for status in Orderstatuses.objects.all():
            status_name_normalized = status.order_statuses_name.lower().replace('ё', 'е')
            if 'отмен' in status_name_normalized:
                cancelled_status_ids.append(status.order_statuses_id)
        
        # Базовый фильтр для заказов (исключаем отмененные)
        base_orders_filter = Orders.objects.filter(orders_date__gte=start_date)
        if cancelled_status_ids:
            base_orders_filter = base_orders_filter.exclude(orders_status_id__in=cancelled_status_ids)
        
        # Общая статистика
        total_orders = base_orders_filter.count()
        total_revenue = base_orders_filter.aggregate(total=Sum('orders_total_amount'))['total'] or Decimal('0')
        avg_order_value = base_orders_filter.aggregate(avg=Avg('orders_total_amount'))['avg'] or Decimal('0')
        
        story.append(safe_paragraph("Общая статистика", heading_style))
        
        # Создаем таблицу с Paragraph для корректного отображения кириллицы
        stats_data = [
            [safe_paragraph('Показатель', normal_style), safe_paragraph('Значение', normal_style)],
            [safe_paragraph('Всего заказов', normal_style), safe_paragraph(safe_text(str(total_orders)), normal_style)],
            [safe_paragraph('Общая выручка', normal_style), safe_paragraph(safe_text(f"{float(total_revenue):,.2f} ₽"), normal_style)],
            [safe_paragraph('Средний чек', normal_style), safe_paragraph(safe_text(f"{float(avg_order_value):,.2f} ₽"), normal_style)],
        ]
        stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f6feb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), font_name),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(stats_table)
        story.append(Spacer(1, 0.2*inch))
        
        # Топ товаров (таблица) - исключаем отмененные заказы
        top_products_table = Orderitems.objects.filter(
            order_items_order__orders_date__gte=start_date
        )
        if cancelled_status_ids:
            top_products_table = top_products_table.exclude(order_items_order__orders_status_id__in=cancelled_status_ids)
        top_products_table = top_products_table.values(
            'order_items_product__products_name'
        ).annotate(
            total_quantity=Sum('order_items_quantity'),
            total_revenue=Sum('order_items_price_at_purchase')
        ).order_by('-total_quantity')[:10]
        
        story.append(safe_paragraph("Топ-10 товаров по продажам", heading_style))
        products_data = [
            [safe_paragraph('Товар', normal_style), 
             safe_paragraph('Количество', normal_style), 
             safe_paragraph('Выручка', normal_style)]
        ]
        for product in top_products_table:
            product_name = product.get('order_items_product__products_name', 'Неизвестно')[:40]
            quantity = str(product.get('total_quantity', 0))
            revenue = f"{float(product.get('total_revenue', 0)):,.2f} ₽"
            products_data.append([
                safe_paragraph(safe_text(product_name), normal_style),
                safe_paragraph(safe_text(quantity), normal_style),
                safe_paragraph(safe_text(revenue), normal_style)
            ])
        
        products_table = Table(products_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
        products_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f6feb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), font_name),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(products_table)
        story.append(Spacer(1, 0.2*inch))
        
        # Статистика по категориям - исключаем отмененные заказы
        category_stats = Orderitems.objects.filter(
            order_items_order__orders_date__gte=start_date
        )
        if cancelled_status_ids:
            category_stats = category_stats.exclude(order_items_order__orders_status_id__in=cancelled_status_ids)
        category_stats = category_stats.values(
            'order_items_product__products_category__categories_name'
        ).annotate(
            total_quantity=Sum('order_items_quantity'),
            total_revenue=Sum('order_items_price_at_purchase')
        ).order_by('-total_revenue')[:10]
        
        story.append(safe_paragraph("Статистика по категориям", heading_style))
        category_data = [
            [safe_paragraph('Категория', normal_style), 
             safe_paragraph('Количество', normal_style), 
             safe_paragraph('Выручка', normal_style)]
        ]
        for cat in category_stats:
            cat_name = cat.get('order_items_product__products_category__categories_name') or 'Без категории'
            quantity = str(cat.get('total_quantity', 0))
            revenue = f"{float(cat.get('total_revenue', 0)):,.2f} ₽"
            category_data.append([
                safe_paragraph(safe_text(cat_name), normal_style),
                safe_paragraph(safe_text(quantity), normal_style),
                safe_paragraph(safe_text(revenue), normal_style)
            ])
        
        category_table = Table(category_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
        category_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f6feb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), font_name),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(category_table)
        story.append(Spacer(1, 0.2*inch))
        
        # ============ СОЗДАНИЕ ГРАФИКОВ ============
        
        # 1. График динамики продаж
        daily_stats = []
        current_date = start_date.date()
        while current_date <= end_date.date():
            day_orders = Orders.objects.filter(
                orders_date__date=current_date
            )
            day_count = day_orders.count()
            day_revenue = day_orders.aggregate(total=Sum('orders_total_amount'))['total'] or Decimal('0')
            daily_stats.append({
                'date': current_date.strftime('%d.%m'),
                'orders': day_count,
                'revenue': float(day_revenue)
            })
            current_date += timedelta(days=1)
        
        if daily_stats:
            story.append(safe_paragraph("Динамика продаж", heading_style))
            fig, ax1 = plt.subplots(figsize=(10, 5))
            dates = [d['date'] for d in daily_stats]
            revenues = [d['revenue'] for d in daily_stats]
            orders = [d['orders'] for d in daily_stats]
            
            ax1.set_xlabel('Дата', fontsize=10)
            ax1.set_ylabel('Выручка (₽)', color='#4BC0C0', fontsize=10)
            line1 = ax1.plot(dates, revenues, color='#4BC0C0', marker='o', linewidth=2, label='Выручка')
            ax1.tick_params(axis='y', labelcolor='#4BC0C0')
            ax1.grid(True, alpha=0.3)
            
            ax2 = ax1.twinx()
            ax2.set_ylabel('Количество заказов', color='#FF6384', fontsize=10)
            line2 = ax2.plot(dates, orders, color='#FF6384', marker='s', linewidth=2, label='Заказы')
            ax2.tick_params(axis='y', labelcolor='#FF6384')
            
            # Поворачиваем подписи дат
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            # Сохраняем график в BytesIO
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            story.append(Image(img_buffer, width=7*inch, height=3.5*inch))
            story.append(Spacer(1, 0.2*inch))
        
        # 2. График топ-10 товаров
        top_products = Orderitems.objects.filter(
            order_items_order__orders_date__gte=start_date
        ).values(
            'order_items_product__products_name'
        ).annotate(
            total_quantity=Sum('order_items_quantity')
        ).order_by('-total_quantity')[:10]
        
        if top_products:
            story.append(safe_paragraph("Топ-10 товаров по продажам (график)", heading_style))
            fig, ax = plt.subplots(figsize=(10, 5))
            product_names = [p.get('order_items_product__products_name', 'Неизвестно')[:30] for p in top_products]
            quantities = [int(p.get('total_quantity', 0)) for p in top_products]
            
            bars = ax.barh(range(len(product_names)), quantities, color='#36A2EB')
            ax.set_yticks(range(len(product_names)))
            ax.set_yticklabels(product_names)
            ax.set_xlabel('Количество продаж', fontsize=10)
            ax.set_title('Топ-10 товаров', fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3, axis='x')
            plt.tight_layout()
            
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            story.append(Image(img_buffer, width=7*inch, height=3.5*inch))
            story.append(Spacer(1, 0.2*inch))
        
        # 3. График продаж по категориям
        category_stats = Orderitems.objects.filter(
            order_items_order__orders_date__gte=start_date
        ).values(
            'order_items_product__products_category__categories_name'
        ).annotate(
            total_revenue=Sum('order_items_price_at_purchase')
        ).order_by('-total_revenue')[:10]
        
        if category_stats:
            story.append(safe_paragraph("Продажи по категориям", heading_style))
            fig, ax = plt.subplots(figsize=(8, 6))
            cat_names = [c.get('order_items_product__products_category__categories_name') or 'Без категории' for c in category_stats]
            revenues = [float(c.get('total_revenue', 0)) for c in category_stats]
            
            colors_pie = plt.cm.Set3(np.linspace(0, 1, len(cat_names)))
            wedges, texts, autotexts = ax.pie(revenues, labels=cat_names, autopct='%1.1f%%', 
                                               colors=colors_pie, startangle=90)
            ax.set_title('Распределение выручки по категориям', fontsize=12, fontweight='bold')
            plt.tight_layout()
            
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            story.append(Image(img_buffer, width=6*inch, height=4.5*inch))
            story.append(Spacer(1, 0.2*inch))
        
        # 4. График заказов по статусам
        status_stats = Orders.objects.filter(
            orders_date__gte=start_date
        ).values(
            'orders_status__order_statuses_name'
        ).annotate(
            count=Count('orders_id')
        )
        
        if status_stats:
            story.append(safe_paragraph("Заказы по статусам", heading_style))
            fig, ax = plt.subplots(figsize=(8, 6))
            status_names = [s.get('orders_status__order_statuses_name') or 'Не указано' for s in status_stats]
            counts = [int(s.get('count', 0)) for s in status_stats]
            
            colors_pie = plt.cm.Pastel1(np.linspace(0, 1, len(status_names)))
            wedges, texts, autotexts = ax.pie(counts, labels=status_names, autopct='%1.1f%%',
                                               colors=colors_pie, startangle=90)
            ax.set_title('Распределение заказов по статусам', fontsize=12, fontweight='bold')
            plt.tight_layout()
            
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            story.append(Image(img_buffer, width=6*inch, height=4.5*inch))
            story.append(Spacer(1, 0.2*inch))
        
        # 5. График способов оплаты
        payment_stats = Orders.objects.filter(
            orders_date__gte=start_date
        ).values(
            'orders_payment_method__payment_methods_name'
        ).annotate(
            count=Count('orders_id')
        )
        
        if payment_stats:
            story.append(safe_paragraph("Способы оплаты", heading_style))
            fig, ax = plt.subplots(figsize=(8, 6))
            payment_names = [p.get('orders_payment_method__payment_methods_name') or 'Не указано' for p in payment_stats]
            counts = [int(p.get('count', 0)) for p in payment_stats]
            
            colors_pie = plt.cm.Set2(np.linspace(0, 1, len(payment_names)))
            wedges, texts, autotexts = ax.pie(counts, labels=payment_names, autopct='%1.1f%%',
                                               colors=colors_pie, startangle=90)
            ax.set_title('Распределение заказов по способам оплаты', fontsize=12, fontweight='bold')
            plt.tight_layout()
            
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            story.append(Image(img_buffer, width=6*inch, height=4.5*inch))
            story.append(Spacer(1, 0.2*inch))
        
        # 6. График способов доставки
        delivery_stats = Orders.objects.filter(
            orders_date__gte=start_date
        ).values(
            'orders_delivery_method__delivery_methods_name'
        ).annotate(
            count=Count('orders_id')
        )
        
        if delivery_stats:
            story.append(safe_paragraph("Способы доставки", heading_style))
            fig, ax = plt.subplots(figsize=(8, 6))
            delivery_names = [d.get('orders_delivery_method__delivery_methods_name') or 'Не указано' for d in delivery_stats]
            counts = [int(d.get('count', 0)) for d in delivery_stats]
            
            colors_pie = plt.cm.Pastel2(np.linspace(0, 1, len(delivery_names)))
            wedges, texts, autotexts = ax.pie(counts, labels=delivery_names, autopct='%1.1f%%',
                                              colors=colors_pie, startangle=90)
            ax.set_title('Распределение заказов по способам доставки', fontsize=12, fontweight='bold')
            plt.tight_layout()
            
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            story.append(Image(img_buffer, width=6*inch, height=4.5*inch))
        
        # Генерируем PDF
        doc.build(story)
        
        # Возвращаем PDF как ответ
        buffer.seek(0)
        response = HttpResponse(buffer.read(), content_type='application/pdf')
        filename = f"analytics_report_{start_date.date().strftime('%Y%m%d')}_{end_date.date().strftime('%Y%m%d')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
        
    except ImportError as e:
        import_name = 'reportlab' if 'reportlab' in str(e) else 'matplotlib'
        messages.error(request, f'Библиотека {import_name} не установлена. Установите её командой: pip install {import_name}')
        return redirect('admin_analytics')
    except Exception as e:
        messages.error(request, f'Ошибка при создании PDF: {str(e)}')
        import traceback
        print(traceback.format_exc())  # Для отладки
        return redirect('admin_analytics')


# ============ УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ ============

@admin_required
def admin_users(request):
    """Список пользователей"""
    users = Users.objects.all().order_by('-users_created_at')
    
    # Поиск
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            users_email__icontains=search_query
        ) | users.filter(
            users_first_name__icontains=search_query
        ) | users.filter(
            users_last_name__icontains=search_query
        )
    
    # Пагинация
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'users': page_obj,
        'search_query': search_query,
    }
    return render(request, 'admin_panel/users/list.html', context)


@admin_required
def admin_user_detail(request, user_id):
    """Детали пользователя"""
    user = get_object_or_404(Users, pk=user_id)
    
    # Заказы пользователя
    user_orders = Orders.objects.filter(orders_user=user).order_by('-orders_date')
    
    # Корзина пользователя
    user_cart = Carts.objects.filter(carts_user=user).first()
    cart_items = Cartitems.objects.filter(cart_items_cart=user_cart) if user_cart else []
    
    context = {
        'user': user,
        'user_orders': user_orders,
        'cart_items': cart_items,
    }
    return render(request, 'admin_panel/users/detail.html', context)


# ============ УПРАВЛЕНИЕ СТАТУСАМИ ЗАКАЗОВ ============

@admin_required
def admin_order_statuses(request):
    """Список статусов заказов"""
    statuses = Orderstatuses.objects.all().order_by('order_statuses_id')
    return render(request, 'admin_panel/order_statuses/list.html', {'statuses': statuses})


@admin_required
def admin_order_status_create(request):
    """Создание статуса заказа"""
    if request.method == 'POST':
        status_name = request.POST.get('order_statuses_name', '').strip()
        if status_name:
            with connection.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO orderstatuses (order_statuses_name)
                       VALUES (%s)
                       RETURNING order_statuses_id""",
                    [status_name]
                )
                status_id = cursor.fetchone()[0]
            messages.success(request, f'Статус "{status_name}" успешно создан!')
            return redirect('admin_order_statuses')
        else:
            messages.error(request, 'Название статуса не может быть пустым!')
    
    return render(request, 'admin_panel/order_statuses/form.html', {'action': 'Создать'})


@admin_required
def admin_order_status_edit(request, status_id):
    """Редактирование статуса заказа"""
    status = get_object_or_404(Orderstatuses, pk=status_id)
    
    if request.method == 'POST':
        status_name = request.POST.get('order_statuses_name', '').strip()
        if status_name:
            with connection.cursor() as cursor:
                cursor.execute(
                    """UPDATE orderstatuses 
                       SET order_statuses_name = %s
                       WHERE order_statuses_id = %s""",
                    [status_name, status_id]
                )
            messages.success(request, f'Статус "{status_name}" успешно обновлен!')
            return redirect('admin_order_statuses')
        else:
            messages.error(request, 'Название статуса не может быть пустым!')
    
    return render(request, 'admin_panel/order_statuses/form.html', {'status': status, 'action': 'Редактировать'})


@admin_required
def admin_order_status_delete(request, status_id):
    """Удаление статуса заказа"""
    status = get_object_or_404(Orderstatuses, pk=status_id)
    
    if request.method == 'POST':
        status_name = status.order_statuses_name
        # Проверяем, используется ли статус в заказах
        orders_count = Orders.objects.filter(orders_status=status).count()
        if orders_count > 0:
            messages.error(request, f'Нельзя удалить статус "{status_name}", так как он используется в {orders_count} заказах!')
            return redirect('admin_order_statuses')
        
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM orderstatuses WHERE order_statuses_id = %s", [status_id])
        messages.success(request, f'Статус "{status_name}" успешно удален!')
        return redirect('admin_order_statuses')
    
    orders_count = Orders.objects.filter(orders_status=status).count()
    return render(request, 'admin_panel/order_statuses/delete.html', {'status': status, 'orders_count': orders_count})


# ============ УПРАВЛЕНИЕ СПОСОБАМИ ОПЛАТЫ ============

@admin_required
def admin_payment_methods(request):
    """Список способов оплаты"""
    payment_methods = Paymentmethods.objects.all().order_by('payment_methods_name')
    return render(request, 'admin_panel/payment_methods/list.html', {'payment_methods': payment_methods})


@admin_required
def admin_payment_method_create(request):
    """Создание способа оплаты"""
    if request.method == 'POST':
        method_name = request.POST.get('payment_methods_name', '').strip()
        if method_name:
            with connection.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO paymentmethods (payment_methods_name)
                       VALUES (%s)
                       RETURNING payment_methods_id""",
                    [method_name]
                )
                method_id = cursor.fetchone()[0]
            messages.success(request, f'Способ оплаты "{method_name}" успешно создан!')
            return redirect('admin_payment_methods')
        else:
            messages.error(request, 'Название способа оплаты не может быть пустым!')
    
    return render(request, 'admin_panel/payment_methods/form.html', {'action': 'Создать'})


@admin_required
def admin_payment_method_edit(request, method_id):
    """Редактирование способа оплаты"""
    method = get_object_or_404(Paymentmethods, pk=method_id)
    
    if request.method == 'POST':
        method_name = request.POST.get('payment_methods_name', '').strip()
        if method_name:
            with connection.cursor() as cursor:
                cursor.execute(
                    """UPDATE paymentmethods 
                       SET payment_methods_name = %s
                       WHERE payment_methods_id = %s""",
                    [method_name, method_id]
                )
            messages.success(request, f'Способ оплаты "{method_name}" успешно обновлен!')
            return redirect('admin_payment_methods')
        else:
            messages.error(request, 'Название способа оплаты не может быть пустым!')
    
    return render(request, 'admin_panel/payment_methods/form.html', {'method': method, 'action': 'Редактировать'})


@admin_required
def admin_payment_method_delete(request, method_id):
    """Удаление способа оплаты"""
    method = get_object_or_404(Paymentmethods, pk=method_id)
    
    if request.method == 'POST':
        method_name = method.payment_methods_name
        # Проверяем, используется ли способ оплаты в заказах
        orders_count = Orders.objects.filter(orders_payment_method=method).count()
        if orders_count > 0:
            messages.error(request, f'Нельзя удалить способ оплаты "{method_name}", так как он используется в {orders_count} заказах!')
            return redirect('admin_payment_methods')
        
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM paymentmethods WHERE payment_methods_id = %s", [method_id])
        messages.success(request, f'Способ оплаты "{method_name}" успешно удален!')
        return redirect('admin_payment_methods')
    
    orders_count = Orders.objects.filter(orders_payment_method=method).count()
    return render(request, 'admin_panel/payment_methods/delete.html', {'method': method, 'orders_count': orders_count})


# ============ УПРАВЛЕНИЕ СПОСОБАМИ ДОСТАВКИ ============

@admin_required
def admin_delivery_methods(request):
    """Список способов доставки"""
    delivery_methods = Deliverymethods.objects.all().order_by('delivery_methods_name')
    return render(request, 'admin_panel/delivery_methods/list.html', {'delivery_methods': delivery_methods})


@admin_required
def admin_delivery_method_create(request):
    """Создание способа доставки"""
    if request.method == 'POST':
        method_name = request.POST.get('delivery_methods_name', '').strip()
        method_cost = request.POST.get('delivery_methods_cost', '0').strip()
        method_description = request.POST.get('delivery_methods_description', '').strip()
        
        if method_name:
            try:
                cost = float(method_cost) if method_cost else 0
            except ValueError:
                cost = 0
            
            with connection.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO deliverymethods (delivery_methods_name, delivery_methods_cost, delivery_methods_description)
                       VALUES (%s, %s, %s)
                       RETURNING delivery_methods_id""",
                    [method_name, cost, method_description or '']
                )
                method_id = cursor.fetchone()[0]
            messages.success(request, f'Способ доставки "{method_name}" успешно создан!')
            return redirect('admin_delivery_methods')
        else:
            messages.error(request, 'Название способа доставки не может быть пустым!')
    
    return render(request, 'admin_panel/delivery_methods/form.html', {'action': 'Создать'})


@admin_required
def admin_delivery_method_edit(request, method_id):
    """Редактирование способа доставки"""
    method = get_object_or_404(Deliverymethods, pk=method_id)
    
    if request.method == 'POST':
        method_name = request.POST.get('delivery_methods_name', '').strip()
        method_cost = request.POST.get('delivery_methods_cost', '0').strip()
        method_description = request.POST.get('delivery_methods_description', '').strip()
        
        if method_name:
            try:
                cost = float(method_cost) if method_cost else 0
            except ValueError:
                cost = 0
            
            with connection.cursor() as cursor:
                cursor.execute(
                    """UPDATE deliverymethods 
                       SET delivery_methods_name = %s, delivery_methods_cost = %s, delivery_methods_description = %s
                       WHERE delivery_methods_id = %s""",
                    [method_name, cost, method_description or '', method_id]
                )
            messages.success(request, f'Способ доставки "{method_name}" успешно обновлен!')
            return redirect('admin_delivery_methods')
        else:
            messages.error(request, 'Название способа доставки не может быть пустым!')
    
    return render(request, 'admin_panel/delivery_methods/form.html', {'method': method, 'action': 'Редактировать'})


@admin_required
def admin_delivery_method_delete(request, method_id):
    """Удаление способа доставки"""
    method = get_object_or_404(Deliverymethods, pk=method_id)
    
    if request.method == 'POST':
        method_name = method.delivery_methods_name
        # Проверяем, используется ли способ доставки в заказах
        orders_count = Orders.objects.filter(orders_delivery_method=method).count()
        if orders_count > 0:
            messages.error(request, f'Нельзя удалить способ доставки "{method_name}", так как он используется в {orders_count} заказах!')
            return redirect('admin_delivery_methods')
        
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM deliverymethods WHERE delivery_methods_id = %s", [method_id])
        messages.success(request, f'Способ доставки "{method_name}" успешно удален!')
        return redirect('admin_delivery_methods')
    
    orders_count = Orders.objects.filter(orders_delivery_method=method).count()
    return render(request, 'admin_panel/delivery_methods/delete.html', {'method': method, 'orders_count': orders_count})


# ============ УДАЛЕНИЕ ИЗОБРАЖЕНИЙ И ХАРАКТЕРИСТИК ============

@admin_required
def admin_product_delete_image(request, product_id, image_id):
    """Удаление изображения товара"""
    product = get_object_or_404(Products, pk=product_id)
    image = get_object_or_404(Productimages, pk=image_id, product_images_product=product)
    
    if request.method == 'POST':
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM productimages WHERE product_images_id = %s", [image_id])
        messages.success(request, 'Изображение успешно удалено!')
        return redirect('admin_product_edit', product_id=product_id)
    
    return render(request, 'admin_panel/products/delete_image.html', {'product': product, 'image': image})


@admin_required
def admin_product_delete_characteristic(request, product_id, characteristic_id):
    """Удаление характеристики товара"""
    product = get_object_or_404(Products, pk=product_id)
    characteristic = get_object_or_404(Productcharacteristics, pk=characteristic_id, product_characteristics_product=product)
    
    if request.method == 'POST':
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM productcharacteristics WHERE product_characteristics_id = %s", [characteristic_id])
        messages.success(request, 'Характеристика успешно удалена!')
        return redirect('admin_product_edit', product_id=product_id)
    
    return render(request, 'admin_panel/products/delete_characteristic.html', {'product': product, 'characteristic': characteristic})
