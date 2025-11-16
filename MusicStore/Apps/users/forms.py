import re
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordResetForm
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.hashers import make_password
from .models import Users


class RegistrationForm(forms.Form):
    email = forms.EmailField(
        label='Email',
        help_text='Например: ivan.petrov@example.com',
    )
    password1 = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput,
        help_text='8–64 символа: заглавная, строчная, цифра и спецсимвол. Без пробелов.',
    )
    password2 = forms.CharField(
        label='Повторите пароль',
        widget=forms.PasswordInput,
        help_text='Введите тот же пароль повторно.',
    )
    first_name = forms.CharField(
        label='Имя', max_length=100,
        help_text='Только буквы или дефис. Например: Иван',
    )
    last_name = forms.CharField(
        label='Фамилия', max_length=100,
        help_text='Только буквы или дефис. Например: Петров',
    )
    middle_name = forms.CharField(
        label='Отчество', max_length=100, required=False,
        help_text='Необязательно. Например: Сергеевич',
    )
    phone = forms.CharField(
        label='Телефон', max_length=20, required=False,
        help_text='Формат: +7XXXXXXXXXX. Например: +79991234567',
    )
    secret_word = forms.CharField(
        label='Секретное слово', max_length=255, required=True,
        help_text='Обязательно для восстановления пароля. Например: Берёза-1975',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Проставляем class и placeholder из help_text
        for name, field in self.fields.items():
            field.widget.attrs.setdefault('class', 'form-control')
            if field.help_text:
                field.widget.attrs.setdefault('placeholder', field.help_text)

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email=email).exists() or Users.objects.filter(users_email=email).exists():
            raise ValidationError('Пользователь с таким email уже существует.')
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            raise ValidationError('Пароли не совпадают.')
        if p1:
            validate_password(p1)
        # Имя/Фамилия/Отчество — только буквы и дефис
        name_pattern = r'^[A-Za-zА-Яа-яЁё\-]+$'
        for key, title in [('first_name','Имя'), ('last_name','Фамилия'), ('middle_name','Отчество')]:
            val = cleaned.get(key)
            if val:
                if not re.match(name_pattern, val):
                    raise ValidationError(f'{title} может содержать только буквы и дефис.')

        # Телефон — простой E.164 для РФ
        phone = cleaned.get('phone')
        if phone:
            if not re.match(r'^\+7\d{10}$', phone):
                raise ValidationError('Телефон должен быть в формате +7XXXXXXXXXX.')
        return cleaned

    def save(self):
        email = self.cleaned_data['email']
        password = self.cleaned_data['password1']
        first_name = self.cleaned_data['first_name']
        last_name = self.cleaned_data['last_name']
        middle_name = self.cleaned_data.get('middle_name')
        phone = self.cleaned_data.get('phone')
        secret_word = self.cleaned_data.get('secret_word')

        # Создаём Django auth пользователя для входа
        auth_user = User.objects.create_user(
            username=email,  # используем email как username
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        # Создаём запись в нашей таблице Users
        Users.objects.create(
            users_email=email,
            users_password_hash=make_password(password),
            users_first_name=first_name,
            users_last_name=last_name,
            users_middle_name=middle_name or None,
            users_phone=phone or None,
            users_secret_word=secret_word,
        )

        return auth_user


class SecretWordPasswordResetForm(PasswordResetForm):
    secret_word = forms.CharField(label='Секретное слово', max_length=255)

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get('email')
        secret_word = cleaned.get('secret_word')
        if email and secret_word:
            # Проверяем привязку секретного слова к email в нашей таблице Users
            if not Users.objects.filter(users_email=email, users_secret_word=secret_word).exists():
                raise ValidationError('Неверное секретное слово для указанного email.')
        return cleaned


class ResetBySecretForm(forms.Form):
    email = forms.EmailField(
        label='Email',
        help_text='Укажите email, который вы использовали при регистрации',
    )
    secret_word = forms.CharField(
        label='Секретное слово', max_length=255,
        help_text='То, что вы указали при регистрации (например: Берёза-1975)',
    )
    new_password1 = forms.CharField(
        label='Новый пароль', widget=forms.PasswordInput,
        help_text='8–64 символа: заглавная, строчная, цифра и спецсимвол. Без пробелов.',
    )
    new_password2 = forms.CharField(
        label='Повторите новый пароль', widget=forms.PasswordInput,
        help_text='Введите тот же пароль повторно.',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _, field in self.fields.items():
            field.widget.attrs.setdefault('class', 'form-control')
            if field.help_text:
                field.widget.attrs.setdefault('placeholder', field.help_text)

    def clean(self):
        cleaned = super().clean()
        email = (cleaned.get('email') or '').strip().lower()
        secret_word = cleaned.get('secret_word')
        p1 = cleaned.get('new_password1')
        p2 = cleaned.get('new_password2')

        # Проверяем пару email + секретное слово
        if not Users.objects.filter(users_email=email, users_secret_word=secret_word).exists():
            raise ValidationError('Неверное секретное слово для указанного email.')

        if p1 and p2 and p1 != p2:
            raise ValidationError('Пароли не совпадают.')
        if p1:
            # Используем строгие валидаторы пароля
            validate_password(p1, user=User(username=email, email=email))

        return cleaned

    def save(self):
        email = self.cleaned_data['email'].strip().lower()
        new_password = self.cleaned_data['new_password1']

        # Обновляем пароль в Django auth_user
        try:
            auth_user = User.objects.get(email=email)
        except User.DoesNotExist:
            auth_user = User.objects.get(username=email)
        auth_user.set_password(new_password)
        auth_user.save()

        # Обновляем хэш в нашей таблице Users
        Users.objects.filter(users_email=email).update(users_password_hash=make_password(new_password))

        return auth_user


class CardForm(forms.Form):
    """Форма для ввода данных банковской карты по ГОСТу"""
    card_number = forms.CharField(
        max_length=19,  # 16 цифр + 3 пробела
        required=True,
        label='Номер карты',
        help_text='Введите 16 цифр номера карты. Пробелы добавляются автоматически. Пример: 4111 1111 1111 1111',
        widget=forms.TextInput(attrs={'placeholder': '4111 1111 1111 1111', 'maxlength': '19'})
    )
    
    card_expiry = forms.CharField(
        max_length=5,
        required=True,
        label='Срок действия',
        help_text='Формат: MM/YY (месяц/год)',
        widget=forms.TextInput(attrs={'placeholder': 'MM/YY', 'maxlength': '5'})
    )
    
    card_cvv = forms.CharField(
        max_length=3,
        required=True,
        label='CVV/CVC',
        help_text='3 цифры на обратной стороне карты',
        widget=forms.PasswordInput(attrs={'placeholder': '123', 'maxlength': '3', 'autocomplete': 'off'})
    )
    
    card_holder_name = forms.CharField(
        max_length=100,
        required=True,
        label='Имя держателя карты',
        help_text='Как указано на карте (только латинские буквы)',
        widget=forms.TextInput(attrs={'placeholder': 'IVAN PETROV'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.setdefault('class', 'form-control')
            if field.help_text:
                field.widget.attrs.setdefault('placeholder', field.help_text)
    
    def clean_card_number(self):
        """Упрощенная валидация номера карты (только проверка на 16 цифр)"""
        card_number = self.cleaned_data.get('card_number', '').strip().replace(' ', '').replace('-', '')
        if not card_number:
            raise ValidationError('Номер карты обязателен для заполнения.')
        
        # Проверка: только цифры, 16 символов
        if not re.match(r'^\d{16}$', card_number):
            raise ValidationError(
                'Номер карты должен содержать ровно 16 цифр. '
                'Введите номер карты в формате: 1234 5678 9012 3456 '
                '(пробелы добавляются автоматически).'
            )
        
        # Убрана проверка по алгоритму Луна - теперь принимаются любые 16 цифр
        return card_number
    
    def clean_card_expiry(self):
        """Валидация срока действия карты (MM/YY)"""
        from datetime import datetime
        card_expiry = self.cleaned_data.get('card_expiry', '').strip()
        if not card_expiry:
            raise ValidationError('Срок действия обязателен для заполнения.')
        
        # Проверка формата MM/YY
        if not re.match(r'^\d{2}/\d{2}$', card_expiry):
            raise ValidationError('Срок действия должен быть в формате MM/YY (например, 12/25).')
        
        month_str, year_str = card_expiry.split('/')
        month = int(month_str)
        year = int(year_str)
        
        # Проверка месяца (01-12)
        if month < 1 or month > 12:
            raise ValidationError('Месяц должен быть от 01 до 12.')
        
        # Проверка, что карта не истекла
        current_year = datetime.now().year % 100
        current_month = datetime.now().month
        
        if year < current_year or (year == current_year and month < current_month):
            raise ValidationError('Срок действия карты истек.')
        
        return card_expiry
    
    def clean_card_cvv(self):
        """Валидация CVV/CVC (3 цифры)"""
        card_cvv = self.cleaned_data.get('card_cvv', '').strip()
        if not card_cvv:
            raise ValidationError('CVV/CVC обязателен для заполнения.')
        
        if not re.match(r'^\d{3}$', card_cvv):
            raise ValidationError('CVV/CVC должен содержать 3 цифры.')
        
        return card_cvv
    
    def clean_card_holder_name(self):
        """Валидация имени держателя карты (только латинские буквы)"""
        card_holder_name = self.cleaned_data.get('card_holder_name', '').strip().upper()
        if not card_holder_name:
            raise ValidationError('Имя держателя обязательно для заполнения.')
        
        # Только латинские буквы, пробелы и дефисы (как на карте)
        if not re.match(r'^[A-Z\s\-]+$', card_holder_name):
            raise ValidationError('Имя держателя должно содержать только латинские буквы, пробелы и дефисы.')
        
        if len(card_holder_name) < 3:
            raise ValidationError('Имя держателя слишком короткое.')
        
        return card_holder_name

