from typing import Iterable, Set

from django.db import connection
from django.db.utils import ProgrammingError, OperationalError
from django.utils import timezone

from .models import Favorites, Usercards
from django.contrib.auth.hashers import make_password, check_password
import base64
import hashlib
from django.conf import settings


def ensure_favorites_table() -> None:
    """
    Создает таблицу favorites, если она отсутствует.
    Нужна для проектов с существующей БД (managed = False).
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS favorites (
                favorites_id SERIAL PRIMARY KEY,
                favorites_user_id INTEGER NOT NULL REFERENCES users (users_id) ON DELETE CASCADE,
                favorites_product_id INTEGER NOT NULL REFERENCES products (products_id) ON DELETE CASCADE,
                favorites_added_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                CONSTRAINT favorites_unique UNIQUE (favorites_user_id, favorites_product_id)
            );
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS favorites_user_idx
            ON favorites (favorites_user_id);
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS favorites_product_idx
            ON favorites (favorites_product_id);
            """
        )


def register_favorite(user_id: int, product_id: int) -> bool:
    """
    Добавляет товар в избранное пользователя.
    Возвращает True, если запись создана, False если уже существовала.
    """
    ensure_favorites_table()
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO favorites (favorites_user_id, favorites_product_id, favorites_added_at)
            VALUES (%s, %s, %s)
            ON CONFLICT (favorites_user_id, favorites_product_id)
            DO NOTHING
            RETURNING favorites_id;
            """,
            [user_id, product_id, timezone.now()],
        )
        if cursor.rowcount:
            cursor.fetchone()
            return True
        return False


def remove_favorite(user_id: int, product_id: int) -> None:
    """Удаляет товар из избранного пользователя."""
    ensure_favorites_table()
    with connection.cursor() as cursor:
        cursor.execute(
            """
            DELETE FROM favorites
            WHERE favorites_user_id = %s AND favorites_product_id = %s;
            """,
            [user_id, product_id],
        )


def get_user_favorite_ids(user_model, product_ids: Iterable[int] | None = None) -> Set[int]:
    """
    Возвращает множество ID товаров, добавленных в избранное.
    Если передан список product_ids, фильтрует по нему.
    """
    try:
        qs = Favorites.objects.filter(favorites_user=user_model)
        if product_ids is not None:
            qs = qs.filter(favorites_product_id__in=list(product_ids))
        return set(qs.values_list('favorites_product_id', flat=True))
    except (ProgrammingError, OperationalError):
        # Таблица отсутствует — создаем и возвращаем пустой набор
        ensure_favorites_table()
        return set()


def ensure_usercards_table() -> None:
    """
    Создает таблицу usercards, если она отсутствует.
    Нужна для проектов с существующей БД (managed = False).
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS usercards (
                usercards_id SERIAL PRIMARY KEY,
                usercards_user_id INTEGER NOT NULL REFERENCES users (users_id) ON DELETE CASCADE,
                usercards_card_number_hash VARCHAR(255) NOT NULL,
                usercards_card_last_four VARCHAR(4) NOT NULL,
                usercards_card_expiry_encrypted VARCHAR(255) NOT NULL,
                usercards_card_cvv_hash VARCHAR(255) NOT NULL,
                usercards_card_holder_name VARCHAR(100) NOT NULL,
                usercards_created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                usercards_updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                usercards_is_default BOOLEAN DEFAULT FALSE
            );
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS usercards_user_idx
            ON usercards (usercards_user_id);
            """
        )


def get_encryption_key():
    """Получает ключ шифрования из настроек"""
    key = getattr(settings, 'CARD_ENCRYPTION_KEY', 'default-secret-key-change-in-production')
    if isinstance(key, str):
        key = key.encode()
    # Используем первые 32 байта для AES или просто base64 кодирование
    return hashlib.sha256(key).digest()[:16]


def encrypt_card_data(data: str) -> str:
    """Шифрует данные карты (простое base64 кодирование с ключом)"""
    key = get_encryption_key()
    # Простое XOR шифрование с ключом
    data_bytes = data.encode('utf-8')
    key_bytes = key * ((len(data_bytes) // len(key)) + 1)
    encrypted = bytes(a ^ b for a, b in zip(data_bytes, key_bytes[:len(data_bytes)]))
    return base64.b64encode(encrypted).decode('utf-8')


def decrypt_card_data(encrypted_data: str) -> str:
    """Расшифровывает данные карты"""
    try:
        key = get_encryption_key()
        encrypted = base64.b64decode(encrypted_data.encode('utf-8'))
        key_bytes = key * ((len(encrypted) // len(key)) + 1)
        decrypted = bytes(a ^ b for a, b in zip(encrypted, key_bytes[:len(encrypted)]))
        return decrypted.decode('utf-8')
    except Exception:
        return ''


def save_user_card(user_id: int, card_number: str, card_expiry: str, card_cvv: str, card_holder_name: str) -> int:
    """
    Сохраняет данные карты пользователя (зашифрованные).
    Возвращает ID сохраненной карты.
    """
    ensure_usercards_table()
    
    # Очищаем номер карты от пробелов
    card_number = card_number.replace(' ', '')
    last_four = card_number[-4:]
    
    # Хэшируем номер карты и CVV
    card_number_hash = make_password(card_number)
    cvv_hash = make_password(card_cvv)
    
    # Шифруем срок действия
    expiry_encrypted = encrypt_card_data(card_expiry)
    
    # Имя держателя в верхний регистр
    card_holder_name = card_holder_name.upper().strip()
    
    with connection.cursor() as cursor:
        # Убираем флаг "по умолчанию" у других карт пользователя
        cursor.execute(
            "UPDATE usercards SET usercards_is_default = FALSE WHERE usercards_user_id = %s",
            [user_id]
        )
        
        # Проверяем, есть ли уже карта у пользователя
        cursor.execute(
            "SELECT usercards_id FROM usercards WHERE usercards_user_id = %s",
            [user_id]
        )
        existing = cursor.fetchone()
        
        if existing:
            # Обновляем существующую карту
            cursor.execute(
                """
                UPDATE usercards 
                SET usercards_card_number_hash = %s,
                    usercards_card_last_four = %s,
                    usercards_card_expiry_encrypted = %s,
                    usercards_card_cvv_hash = %s,
                    usercards_card_holder_name = %s,
                    usercards_updated_at = NOW(),
                    usercards_is_default = TRUE
                WHERE usercards_user_id = %s
                RETURNING usercards_id
                """,
                [card_number_hash, last_four, expiry_encrypted, cvv_hash, card_holder_name, user_id]
            )
            return cursor.fetchone()[0]
        else:
            # Создаем новую карту
            cursor.execute(
                """
                INSERT INTO usercards (
                    usercards_user_id, usercards_card_number_hash, usercards_card_last_four,
                    usercards_card_expiry_encrypted, usercards_card_cvv_hash, usercards_card_holder_name,
                    usercards_is_default, usercards_created_at, usercards_updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, TRUE, NOW(), NOW())
                RETURNING usercards_id
                """,
                [user_id, card_number_hash, last_four, expiry_encrypted, cvv_hash, card_holder_name]
            )
            return cursor.fetchone()[0]


def get_user_card(user_model):
    """Получает сохраненную карту пользователя"""
    ensure_usercards_table()
    try:
        return Usercards.objects.filter(usercards_user=user_model).first()
    except (ProgrammingError, OperationalError):
        ensure_usercards_table()
        return None


def get_user_card_data_for_form(user_model):
    """Получает данные карты пользователя для заполнения формы (только расшифрованные данные)"""
    card = get_user_card(user_model)
    if not card:
        return None
    
    try:
        # Расшифровываем срок действия
        expiry = decrypt_card_data(card.usercards_card_expiry_encrypted)
        
        return {
            'card_holder_name': card.usercards_card_holder_name,
            'card_expiry': expiry if expiry else '',
            'card_last_four': card.usercards_card_last_four,
        }
    except Exception:
        return {
            'card_holder_name': card.usercards_card_holder_name if hasattr(card, 'usercards_card_holder_name') else '',
            'card_expiry': '',
            'card_last_four': card.usercards_card_last_four if hasattr(card, 'usercards_card_last_four') else '',
        }


def delete_user_card(user_id: int) -> None:
    """Удаляет карту пользователя"""
    ensure_usercards_table()
    with connection.cursor() as cursor:
        cursor.execute(
            "DELETE FROM usercards WHERE usercards_user_id = %s",
            [user_id]
        )

