from rest_framework import generics, permissions
from .models import User
from .serializers import UserSerializer

class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Просмотр и редактирование профиля.
    Только для авторизованных пользователей.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'patch']
    
    def get_object(self):
        # Возвращает текущего пользователя, залогиненного через токен
        return self.request.user