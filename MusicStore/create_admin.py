#!/usr/bin/env python
"""Скрипт для создания администратора"""
import os
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MusicStore.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Создаем или обновляем администратора
username = 'igor'
password = '1'

try:
    user = User.objects.get(username=username)
    print(f"✓ Пользователь '{username}' уже существует")
    user.set_password(password)
    user.is_staff = True
    user.is_superuser = True
    user.is_active = True
    user.save()
    print(f"✓ Права администратора обновлены")
except User.DoesNotExist:
    user = User.objects.create_user(
        username=username,
        email='igor@musicstore.ru',
        password=password,
        is_staff=True,
        is_superuser=True,
        is_active=True
    )
    print(f"✓ Администратор '{username}' создан")

print(f"\nДанные для входа:")
print(f"  Логин: {username}")
print(f"  Пароль: {password}")
print(f"  URL: http://127.0.0.1:8000/admin/")
print(f"\n✓ Статус: {'Суперпользователь' if user.is_superuser else 'Обычный пользователь'}")
print(f"✓ Доступ к админке: {'Да' if user.is_staff else 'Нет'}")
print(f"✓ Активен: {'Да' if user.is_active else 'Нет'}")

