from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import connection
from django.utils import timezone
from .models import Carts, Cartitems
from Apps.users.models import Users
from Apps.catalog.models import Products


@login_required
def add_to_cart(request, product_id):
    """Добавление товара в корзину"""
    try:
        user_model = Users.objects.get(users_email=request.user.email)
        product = get_object_or_404(Products, products_id=product_id)
        
        # Получаем количество из запроса (по умолчанию 1)
        quantity = int(request.GET.get('quantity', 1))
        if quantity < 1:
            quantity = 1
        
        # Проверяем наличие товара на складе
        if product.products_stock < quantity:
            messages.warning(request, f'Недостаточно товара на складе. В наличии: {product.products_stock} шт.')
            return redirect('catalog')
        
        # Получаем или создаем корзину для пользователя
        cart = Carts.objects.filter(carts_user=user_model).first()
        if not cart:
            # Создаем новую корзину через raw SQL, так как managed = False
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO carts (carts_user_id, carts_created_at) VALUES (%s, %s) RETURNING carts_id",
                    [user_model.users_id, timezone.now()]
                )
                cart_id = cursor.fetchone()[0]
                cart = Carts.objects.get(carts_id=cart_id)
        
        # Проверяем, есть ли уже этот товар в корзине
        cart_item = Cartitems.objects.filter(
            cart_items_cart=cart,
            cart_items_product=product
        ).first()
        
        if cart_item:
            # Если товар уже есть, увеличиваем количество
            new_quantity = cart_item.cart_items_quantity + quantity
            if new_quantity > product.products_stock:
                messages.warning(request, f'Недостаточно товара на складе. Максимальное количество: {product.products_stock} шт.')
                return redirect('catalog')
            
            # Обновляем количество через raw SQL
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE cartitems SET cart_items_quantity = %s WHERE cart_items_id = %s",
                    [new_quantity, cart_item.cart_items_id]
                )
            messages.success(request, f'Количество товара "{product.products_name}" обновлено в корзине.')
        else:
            # Создаем новый элемент корзины через raw SQL
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO cartitems (cart_items_cart_id, cart_items_product_id, cart_items_quantity, cart_items_added_at) VALUES (%s, %s, %s, %s) RETURNING cart_items_id",
                    [cart.carts_id, product.products_id, quantity, timezone.now()]
                )
            messages.success(request, f'Товар "{product.products_name}" добавлен в корзину.')
        
        # Перенаправляем обратно на каталог или на страницу корзины
        redirect_to = request.GET.get('next', 'catalog')
        if redirect_to == 'cart':
            return redirect('cart')
        return redirect('catalog')
        
    except Users.DoesNotExist:
        messages.error(request, 'Профиль пользователя не найден.')
        return redirect('catalog')
    except Exception as e:
        messages.error(request, f'Ошибка при добавлении товара в корзину: {str(e)}')
        return redirect('catalog')


@login_required
def cart_view(request):
    """Страница корзины пользователя"""
    try:
        user_model = Users.objects.get(users_email=request.user.email)
        cart = Carts.objects.filter(carts_user=user_model).first()
        
        if cart:
            cart_items = Cartitems.objects.filter(cart_items_cart=cart)
        else:
            cart_items = []
        
        # Вычисляем сумму с учетом количества каждого товара
        cart_items_with_total = []
        total = 0
        for item in cart_items:
            item_total = float(item.cart_items_quantity) * float(item.cart_items_product.products_price)
            total += item_total
            cart_items_with_total.append({
                'item': item,
                'item_total': item_total,
            })
        
        context = {
            'cart': cart,
            'cart_items_with_total': cart_items_with_total,
            'total': total,
        }
    except Users.DoesNotExist:
        messages.error(request, 'Профиль пользователя не найден.')
        return redirect('home')
    
    return render(request, 'cart/cart.html', context)


@login_required
def remove_from_cart(request, item_id):
    """Удаление товара из корзины"""
    try:
        user_model = Users.objects.get(users_email=request.user.email)
        cart = Carts.objects.filter(carts_user=user_model).first()
        
        if not cart:
            messages.error(request, 'Корзина не найдена.')
            return redirect('cart')
        
        # Проверяем, что товар принадлежит корзине пользователя
        cart_item = Cartitems.objects.filter(
            cart_items_id=item_id,
            cart_items_cart=cart
        ).first()
        
        if not cart_item:
            messages.error(request, 'Товар не найден в корзине.')
            return redirect('cart')
        
        # Удаляем товар через raw SQL
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM cartitems WHERE cart_items_id = %s",
                [item_id]
            )
        
        messages.success(request, f'Товар "{cart_item.cart_items_product.products_name}" удален из корзины.')
        
    except Users.DoesNotExist:
        messages.error(request, 'Профиль пользователя не найден.')
        return redirect('cart')
    except Exception as e:
        messages.error(request, f'Ошибка при удалении товара из корзины: {str(e)}')
    
    return redirect('cart')
