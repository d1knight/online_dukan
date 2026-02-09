from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Модель пользователя с дополнительными полями"""
    ROLES = (('admin', 'Admin'), ('client', 'Client'))
    
    role = models.CharField(max_length=10, choices=ROLES, default='client')
    phone = models.CharField(max_length=20, blank=True, unique=True) 
    address = models.TextField(blank=True)
    
    # Поля для Telegram авторизации
    telegram_chat_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    verification_code = models.CharField(max_length=6, null=True, blank=True)
    code_expires_at = models.DateTimeField(null=True, blank=True)
    
    REQUIRED_FIELDS = ['phone']

    def __str__(self):
        return self.username or self.phone

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'