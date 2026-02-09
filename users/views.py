from rest_framework import generics, permissions
from .models import User
from .serializers import UserSerializer


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Просмотр и редактирование профиля пользователя
    GET - получить свой профиль
    PATCH - обновить профиль (first_name, last_name, address)
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'patch']
    
    def get_object(self):
        return self.request.user