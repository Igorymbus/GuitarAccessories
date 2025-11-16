from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .forms import SecretWordPasswordResetForm

urlpatterns = [
    # Корневой путь всегда открывает форму регистрации
    path('', views.register_view, name='auth-entry'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('password-change/', views.password_change_view, name='password_change'),
    path('password-reset-secret/', views.password_reset_by_secret_view, name='password_reset_secret'),
    # Восстановление пароля
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='users/password_reset.html', form_class=SecretWordPasswordResetForm), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='users/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='users/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='users/password_reset_complete.html'), name='password_reset_complete'),
]


