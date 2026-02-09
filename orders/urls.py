from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, CheckoutView

app_name = 'orders'

router = DefaultRouter()
router.register(r'', OrderViewSet, basename='order')

urlpatterns = [
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('', include(router.urls)),
]