from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from .forms import RegistrationForm, ResetBySecretForm, CardForm
from .utils import save_user_card, get_user_card, ensure_usercards_table, delete_user_card, get_user_card_data_for_form
from django.contrib.auth.decorators import login_required
from .models import Users


def entry_view(request):
    """Root entry: show registration for anonymous, otherwise go to home."""
    if request.user.is_authenticated:
        return redirect('home')
    return redirect('register')


def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Аккаунт создан. Выполнен вход.')
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Исправьте ошибки в форме.')
    else:
        form = RegistrationForm()
    return render(request, 'users/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, 'Вы вошли в систему.')
            return redirect('home')
        else:
            messages.error(request, 'Неверные учетные данные.')
    else:
        form = AuthenticationForm(request)
    return render(request, 'users/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'Вы вышли из системы.')
    return redirect('home')


@login_required
def password_change_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            
            # Обновляем пароль и в таблице Apps.users.Users
            try:
                from django.contrib.auth.hashers import make_password
                app_user = Users.objects.get(users_email=request.user.email)
                app_user.users_password_hash = make_password(form.cleaned_data['new_password1'])
                app_user.save()
            except Users.DoesNotExist:
                pass
            
            messages.success(request, 'Ваш пароль был успешно изменен.')
            return redirect('profile')
        else:
            messages.error(request, 'Исправьте ошибки в форме.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'users/password_change.html', {'form': form})


def password_reset_by_secret_view(request):
    """Восстановление пароля по секретному слову (не требует авторизации)"""
    if request.method == 'POST':
        form = ResetBySecretForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            new_password = form.cleaned_data['new_password1']
            
            from django.contrib.auth.hashers import make_password
            from django.contrib.auth.models import User
            
            try:
                # Обновляем пароль в Django User
                user = User.objects.get(email=email)
                user.set_password(new_password)
                user.save()
                
                # Обновляем пароль в Apps.users.Users
                app_user = Users.objects.get(users_email=email)
                app_user.users_password_hash = make_password(new_password)
                app_user.save()
                
                messages.success(request, 'Ваш пароль успешно обновлен. Теперь вы можете войти с новым паролем.')
                return redirect('login')
            except User.DoesNotExist:
                messages.error(request, 'Пользователь с таким email не найден.')
            except Users.DoesNotExist:
                messages.error(request, 'Пользователь с таким email не найден.')
            except Exception as e:
                messages.error(request, f'Ошибка при обновлении пароля: {str(e)}')
    else:
        form = ResetBySecretForm()
    return render(request, 'users/password_reset_secret.html', {'form': form})


@login_required
def profile_view(request):
    """Страница профиля пользователя"""
    try:
        user_model = Users.objects.get(users_email=request.user.email)
        ensure_usercards_table()
        
        # Получаем сохраненную карту пользователя
        saved_card = get_user_card(user_model)
        
        # Обработка формы карты
        card_form = None
        if request.method == 'POST' and 'card_form' in request.POST:
            card_form = CardForm(request.POST)
            if card_form.is_valid():
                try:
                    save_user_card(
                        user_id=user_model.users_id,
                        card_number=card_form.cleaned_data['card_number'],
                        card_expiry=card_form.cleaned_data['card_expiry'],
                        card_cvv=card_form.cleaned_data['card_cvv'],
                        card_holder_name=card_form.cleaned_data['card_holder_name']
                    )
                    messages.success(request, 'Данные банковской карты успешно сохранены!')
                    saved_card = get_user_card(user_model)  # Обновляем данные карты
                    # Заполняем форму данными из сохраненной карты
                    card_data = get_user_card_data_for_form(user_model)
                    if card_data:
                        card_form = CardForm(initial={
                            'card_holder_name': card_data['card_holder_name'],
                            'card_expiry': card_data['card_expiry'],
                        })
                    else:
                        card_form = CardForm()
                except Exception as e:
                    messages.error(request, f'Ошибка при сохранении данных карты: {str(e)}')
        elif request.method == 'POST' and 'delete_card' in request.POST:
            # Удаление карты
            try:
                delete_user_card(user_model.users_id)
                messages.success(request, 'Данные банковской карты удалены.')
                saved_card = None
                card_form = CardForm()
            except Exception as e:
                messages.error(request, f'Ошибка при удалении карты: {str(e)}')
                # Заполняем форму данными из сохраненной карты при ошибке
                card_data = get_user_card_data_for_form(user_model)
                if card_data:
                    card_form = CardForm(initial={
                        'card_holder_name': card_data['card_holder_name'],
                        'card_expiry': card_data['card_expiry'],
                    })
                else:
                    card_form = CardForm()
        else:
            # Заполняем форму данными из сохраненной карты, если она есть
            card_data = get_user_card_data_for_form(user_model)
            if card_data:
                card_form = CardForm(initial={
                    'card_holder_name': card_data['card_holder_name'],
                    'card_expiry': card_data['card_expiry'],
                })
            else:
                card_form = CardForm()
        
        context = {
            'user': request.user,
            'user_profile': user_model,
            'card_form': card_form,
            'saved_card': saved_card,
        }
    except Users.DoesNotExist:
        messages.error(request, 'Профиль пользователя не найден.')
        return redirect('home')
    
    return render(request, 'users/profile.html', context)

# Create your views here.
