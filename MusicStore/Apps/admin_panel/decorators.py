from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def admin_required(view_func):
    """Декоратор для проверки прав администратора"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Для доступа к админ-панели необходимо войти в систему.')
            return redirect('login')
        
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, 'У вас нет прав для доступа к админ-панели.')
            return redirect('home')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view

