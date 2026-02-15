from rest_framework import generics, permissions
from .models import User
from .serializers import UserSerializer

#21.01.2026
# Текгана авторизациядан откен пайдаланыушы редактировать или коре алады
class UserProfileView(generics.RetrieveUpdateAPIView):

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'patch']
    
    def get_object(self):
        # усы токен аркала логин кылган пайдаланыушына кайтарады
        return self.request.user