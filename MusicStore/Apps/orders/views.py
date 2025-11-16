from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import connection, transaction
from django.utils import timezone
from django.utils.html import format_html
from django.urls import reverse
from .models import Orders, Orderitems, Orderstatuses, Orderhistory
from Apps.users.models import Users, Addresses
from Apps.users.utils import get_user_card, ensure_usercards_table
from Apps.cart.models import Carts, Cartitems
from Apps.payments.models import Paymentmethods, Deliverymethods, Payments
from .forms import OrderForm


@login_required
def checkout_view(request):
    """Страница оформления заказа"""
    try:
        user_model = Users.objects.get(users_email=request.user.email)
        
        # Получаем корзину пользователя
        cart = Carts.objects.filter(carts_user=user_model).first()
        if not cart:
            messages.warning(request, 'Ваша корзина пуста.')
            return redirect('cart')
        
        cart_items = Cartitems.objects.filter(cart_items_cart=cart)
        if not cart_items.exists():
            messages.warning(request, 'Ваша корзина пуста.')
            return redirect('cart')
        
        # Проверяем наличие товаров на складе
        for item in cart_items:
            if item.cart_items_product.products_stock < item.cart_items_quantity:
                messages.error(
                    request,
                    f'Товар "{item.cart_items_product.products_name}" недоступен в количестве {item.cart_items_quantity}. '
                    f'В наличии: {item.cart_items_product.products_stock} шт.'
                )
                return redirect('cart')
        
        # Вычисляем общую сумму
        total = sum(
            float(item.cart_items_quantity) * float(item.cart_items_product.products_price)
            for item in cart_items
        )
        
        # Получаем способы доставки и оплаты (исключаем самовывоз)
        delivery_methods = Deliverymethods.objects.exclude(
            delivery_methods_name__icontains='самовывоз'
        ).exclude(
            delivery_methods_name__icontains='pickup'
        ).exclude(
            delivery_methods_name__icontains='self_pickup'
        )
        payment_methods = Paymentmethods.objects.all()
        
        existing_addresses = Addresses.objects.filter(addresses_user=user_model)
        
        ensure_usercards_table()
        
        # Получаем сохраненную карту пользователя
        saved_card = get_user_card(user_model)
        
        # Подготавливаем информацию о способах доставки с ценами (нужно для контекста в любом случае)
        delivery_info = []
        for method in delivery_methods:
            delivery_info.append({
                'method': method,
                'cost': float(method.delivery_methods_cost or 0),
            })
        
        if request.method == 'POST':
            form = OrderForm(request.POST)
            if form.is_valid():
                # Проверка наличия сохраненной карты при выборе оплаты картой
                payment_method = form.cleaned_data.get('payment_method')
                if payment_method:
                    payment_method_name = payment_method.payment_methods_name.lower()
                    is_card_payment = (
                        'карта' in payment_method_name or 
                        'card' in payment_method_name or 
                        'кредит' in payment_method_name or
                        'credit' in payment_method_name
                    )
                    
                    if is_card_payment and not saved_card:
                        profile_url = reverse('profile')
                        messages.error(
                            request,
                            format_html(
                                'Для оплаты картой необходимо сохранить данные карты в профиле. '
                                'Пожалуйста, перейдите в <a href="{}" class="alert-link">профиль</a> и добавьте данные карты.',
                                profile_url
                            )
                        )
                        form = OrderForm(request.POST)  # Перезагружаем форму с данными
                        return render(request, 'orders/checkout.html', {
                            'form': form,
                            'cart_items': cart_items,
                            'total': total,
                            'delivery_methods': delivery_methods,
                            'delivery_info': delivery_info,
                            'payment_methods': payment_methods,
                            'has_saved_card': False,
                        })
                
                try:
                    with transaction.atomic():
                        # Получаем или создаем адрес на основе введенных данных
                        street = form.cleaned_data['street']
                        city = form.cleaned_data['city']
                        zip_code = form.cleaned_data['zip_code']
                        country = form.cleaned_data.get('country', 'Россия')
                        
                        address = existing_addresses.filter(
                            addresses_street=street,
                            addresses_city=city,
                            addresses_zip_code=zip_code,
                            addresses_country=country
                        ).first()
                        
                        if not address:
                            with connection.cursor() as cursor:
                                cursor.execute(
                                    """INSERT INTO addresses 
                                       (addresses_user_id, addresses_street, addresses_city, addresses_zip_code, 
                                        addresses_country, addresses_is_default, addresses_created_at) 
                                       VALUES (%s, %s, %s, %s, %s, %s, %s) 
                                       RETURNING addresses_id""",
                                    [
                                        user_model.users_id,
                                        street,
                                        city,
                                        zip_code,
                                        country,
                                        not existing_addresses.exists(),
                                        timezone.now()
                                    ]
                                )
                                address_id = cursor.fetchone()[0]
                                address = Addresses.objects.get(addresses_id=address_id)
                        
                        # Получаем способ доставки и оплаты
                        delivery_method = form.cleaned_data['delivery_method']
                        payment_method = form.cleaned_data['payment_method']
                        comment = form.cleaned_data.get('comment', '')
                        
                        # Добавляем стоимость доставки к общей сумме
                        delivery_cost = float(delivery_method.delivery_methods_cost or 0)
                        total_with_delivery = total + delivery_cost
                        
                        # Получаем начальный статус заказа (обычно "Новый" или "Ожидает оплаты")
                        default_status = Orderstatuses.objects.filter(
                            order_statuses_name__icontains='новый'
                        ).first()
                        if not default_status:
                            default_status = Orderstatuses.objects.first()
                        
                        if not default_status:
                            messages.error(request, 'Ошибка: не найден статус заказа в системе.')
                            return redirect('cart')
                        
                        # Создаем заказ через raw SQL
                        with connection.cursor() as cursor:
                            cursor.execute(
                                """INSERT INTO orders 
                                   (orders_user_id, orders_total_amount, orders_date, orders_status_id, 
                                    orders_payment_method_id, orders_delivery_method_id, orders_address_id, orders_comment) 
                                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s) 
                                   RETURNING orders_id""",
                                [
                                    user_model.users_id,
                                    total_with_delivery,
                                    timezone.now(),
                                    default_status.order_statuses_id,
                                    payment_method.payment_methods_id,
                                    delivery_method.delivery_methods_id,
                                    address.addresses_id,
                                    comment or None
                                ]
                            )
                            order_id = cursor.fetchone()[0]
                            order = Orders.objects.get(orders_id=order_id)
                        
                        # Создаем элементы заказа
                        for cart_item in cart_items:
                            product = cart_item.cart_items_product
                            quantity = cart_item.cart_items_quantity
                            price = product.products_price
                            
                            with connection.cursor() as cursor:
                                cursor.execute(
                                    """INSERT INTO orderitems 
                                       (order_items_order_id, order_items_product_id, order_items_quantity, 
                                        order_items_price_at_purchase) 
                                       VALUES (%s, %s, %s, %s) 
                                       RETURNING order_items_id""",
                                    [order.orders_id, product.products_id, quantity, price]
                                )
                            
                            # Уменьшаем количество товара на складе
                            with connection.cursor() as cursor:
                                cursor.execute(
                                    "UPDATE products SET products_stock = products_stock - %s WHERE products_id = %s",
                                    [quantity, product.products_id]
                                )
                        
                        # Создаем запись в истории заказов
                        # Используем правильное имя столбца из db_column
                        with connection.cursor() as cursor:
                            cursor.execute(
                                """INSERT INTO orderhistory 
                                   (order_history_order_id, order_history_status_id, order_history_changed_at, 
                                    order_history_changed_by) 
                                   VALUES (%s, %s, %s, %s) 
                                   RETURNING order_history_id""",
                                [order.orders_id, default_status.order_statuses_id, timezone.now(), user_model.users_id]
                            )
                        
                        # Создаем запись о платеже
                        payment_status = 'pending'  # Ожидает оплаты
                        with connection.cursor() as cursor:
                            cursor.execute(
                                """INSERT INTO payments 
                                   (payments_order_id, payments_amount, payments_date, payments_status) 
                                   VALUES (%s, %s, %s, %s) 
                                   RETURNING payments_id""",
                                [order.orders_id, total_with_delivery, timezone.now(), payment_status]
                            )
                        
                        # Очищаем корзину
                        with connection.cursor() as cursor:
                            cursor.execute(
                                "DELETE FROM cartitems WHERE cart_items_cart_id = %s",
                                [cart.carts_id]
                            )
                        
                        messages.success(
                            request,
                            f'Заказ №{order.orders_id} успешно оформлен! '
                            f'Общая сумма: {total_with_delivery:.2f} ₽'
                        )
                        return redirect('order_success', order_id=order.orders_id)
                        
                except Exception as e:
                    messages.error(request, f'Ошибка при оформлении заказа: {str(e)}')
                    return redirect('cart')
        else:
            initial_data = {}
            default_address = existing_addresses.filter(addresses_is_default=True).first() or existing_addresses.first()
            if default_address:
                initial_data = {
                    'street': default_address.addresses_street or '',
                    'city': default_address.addresses_city or '',
                    'zip_code': default_address.addresses_zip_code or '',
                    'country': default_address.addresses_country or 'Россия',
                }
            form = OrderForm(initial=initial_data)
        
        context = {
            'form': form,
            'cart_items': cart_items,
            'total': total,
            'delivery_methods': delivery_methods,
            'delivery_info': delivery_info,
            'payment_methods': payment_methods,
            'has_saved_card': saved_card is not None,
            'saved_card': saved_card,
        }
        return render(request, 'orders/checkout.html', context)
        
    except Users.DoesNotExist:
        messages.error(request, 'Профиль пользователя не найден.')
        return redirect('home')


@login_required
def order_success_view(request, order_id):
    """Страница успешного оформления заказа"""
    try:
        user_model = Users.objects.get(users_email=request.user.email)
        order = get_object_or_404(Orders, orders_id=order_id, orders_user=user_model)
        
        order_items = Orderitems.objects.filter(order_items_order=order)
        total = sum(
            float(item.order_items_quantity) * float(item.order_items_price_at_purchase)
            for item in order_items
        )
        
        context = {
            'order': order,
            'order_items': order_items,
            'total': total,
        }
        return render(request, 'orders/order_success.html', context)
    except Users.DoesNotExist:
        messages.error(request, 'Профиль пользователя не найден.')
        return redirect('home')


@login_required
def orders_view(request):
    """Страница списка заказов пользователя"""
    try:
        user_model = Users.objects.get(users_email=request.user.email)
        orders = Orders.objects.filter(orders_user=user_model).order_by('-orders_date')
        
        # Добавляем информацию о товарах в каждом заказе
        orders_with_items = []
        for order in orders:
            order_items = Orderitems.objects.filter(order_items_order=order)
            # Сумма товаров без доставки (приводим к float)
            items_total = float(sum(float(item.order_items_quantity) * float(item.order_items_price_at_purchase) for item in order_items))
            # Итоговая сумма с доставкой (используем orders_total_amount, который уже включает доставку)
            total_with_delivery = float(order.orders_total_amount) if order.orders_total_amount else items_total
            # Стоимость доставки = итоговая сумма - сумма товаров
            delivery_cost = total_with_delivery - items_total
            
            # Проверяем, можно ли отменить заказ (не отменен и не доставлен)
            order_status_name = order.orders_status.order_statuses_name.lower().replace('ё', 'е')
            is_cancelled = 'отмен' in order_status_name
            is_delivered = 'доставлен' in order_status_name
            can_cancel = not is_cancelled and not is_delivered
            
            orders_with_items.append({
                'order': order,
                'items': order_items,
                'items_total': items_total,  # Сумма только товаров
                'delivery_cost': delivery_cost,  # Стоимость доставки
                'total': total_with_delivery,  # Итоговая сумма с доставкой
                'can_cancel': can_cancel,  # Можно ли отменить заказ
            })
        
        context = {
            'orders_with_items': orders_with_items,
        }
    except Users.DoesNotExist:
        messages.error(request, 'Профиль пользователя не найден.')
        return redirect('home')
    
    return render(request, 'orders/orders.html', context)


@login_required
def cancel_order_view(request, order_id):
    """Отмена заказа клиентом с возвратом товаров на склад"""
    try:
        user_model = Users.objects.get(users_email=request.user.email)
        order = get_object_or_404(Orders, pk=order_id, orders_user=user_model)
        
        # Проверяем, что заказ принадлежит текущему пользователю
        if order.orders_user != user_model:
            messages.error(request, 'У вас нет доступа к этому заказу.')
            return redirect('orders')
        
        # Проверяем текущий статус заказа
        order_status_name = order.orders_status.order_statuses_name.lower().replace('ё', 'е')
        is_cancelled = 'отмен' in order_status_name
        is_delivered = 'доставлен' in order_status_name
        
        if is_cancelled:
            messages.warning(request, f'Заказ #{order_id} уже отменен.')
            return redirect('orders')
        
        if is_delivered:
            messages.warning(request, f'Нельзя отменить доставленный заказ #{order_id}.')
            return redirect('orders')
        
        # Находим статус "Отменён"
        cancelled_status = None
        for status in Orderstatuses.objects.all():
            status_name_normalized = status.order_statuses_name.lower().replace('ё', 'е')
            if 'отмен' in status_name_normalized:
                cancelled_status = status
                break
        
        if not cancelled_status:
            messages.error(request, 'Статус "Отменён" не найден в системе. Обратитесь к администратору.')
            return redirect('orders')
        
        # Используем транзакцию для атомарности операций
        with transaction.atomic():
            # Обновляем статус заказа
            with connection.cursor() as cursor:
                cursor.execute(
                    """UPDATE orders 
                       SET orders_status_id = %s
                       WHERE orders_id = %s""",
                    [cancelled_status.order_statuses_id, order_id]
                )
            
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
            
            if order_items_data:
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
                messages.warning(request, f'Заказ #{order_id} отменен, но в заказе нет товаров для возврата на склад.')
        
        return redirect('orders')
        
    except Users.DoesNotExist:
        messages.error(request, 'Профиль пользователя не найден.')
        return redirect('home')
    except Exception as e:
        messages.error(request, f'Ошибка при отмене заказа: {str(e)}')
        return redirect('orders')
