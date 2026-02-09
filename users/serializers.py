from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор профиля пользователя"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'phone', 'address', 'role']
        read_only_fields = ['username', 'phone', 'role']