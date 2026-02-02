from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView # TokenObtainPairView kerek emes
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from api.views import *

schema_view = get_schema_view(
   openapi.Info(title="Online Dukan API", default_version='v1'),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

router = DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'orders', OrderViewSet, basename='orders')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    
    
    # Refresh token kerek boladı (Telegramnan alǵan tokendi jańalaw ushın)
    path('api/token/refresh/', TokenRefreshView.as_view()),
    
    # Telegram Auth
    path('api/telegram/webhook/', TelegramWebhookView.as_view()),
    path('api/auth/telegram/', TelegramAuthView.as_view()),
    
    
    # Profile
    path('api/profile/', UserProfileView.as_view()), 

    # Shop
    path('api/checkout/', CheckoutView.as_view()),
    
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0)),
] 

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)