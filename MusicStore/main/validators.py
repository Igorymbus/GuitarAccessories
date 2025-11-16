import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class GOSTPasswordValidator:
    """Строгая проверка пароля (RU):
    - длина 8–64
    - минимум: 1 заглавная, 1 строчная, 1 цифра, 1 спецсимвол
    - без пробелов
    - не совпадает с email/именем/фамилией
    """

    def __init__(self, min_length: int = 8, max_length: int = 64):
        self.min_length = min_length
        self.max_length = max_length

    def validate(self, password, user=None):
        if not (self.min_length <= len(password) <= self.max_length):
            raise ValidationError(
                _('Пароль должен содержать от %(min)d до %(max)d символов.'),
                code='password_length',
                params={'min': self.min_length, 'max': self.max_length},
            )

        if ' ' in password:
            raise ValidationError(_('Пароль не должен содержать пробелы.'), code='password_spaces')

        # Категории символов (латиница и кириллица)
        has_upper = re.search(r'[A-ZА-ЯЁ]', password) is not None
        has_lower = re.search(r'[a-zа-яё]', password) is not None
        has_digit = re.search(r'\d', password) is not None
        has_symbol = re.search(r'[~!@#$%^&*()_+\-={}\[\]|:";\'\\<>,.?/`]', password) is not None

        if not (has_upper and has_lower and has_digit and has_symbol):
            raise ValidationError(
                _('Пароль должен содержать как минимум: заглавную букву, строчную букву, цифру и спецсимвол.'),
                code='password_character_classes',
            )

        # Не совпадает и не содержит очевидные персональные данные
        if user is not None:
            checks = []
            username = getattr(user, 'username', None) or ''
            email = getattr(user, 'email', None) or ''
            first_name = getattr(user, 'first_name', '') or ''
            last_name = getattr(user, 'last_name', '') or ''
            checks.extend([username, email, first_name, last_name])
            for v in checks:
                v = str(v).strip()
                if v and v.lower() in password.lower():
                    raise ValidationError(_('Пароль не должен содержать персональные данные.'), code='password_personal')

    def get_help_text(self):
        return _('Пароль: 8–64 символа, минимум 1 заглавная, 1 строчная, 1 цифра и 1 спецсимвол, без пробелов.')


