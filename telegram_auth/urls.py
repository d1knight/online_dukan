from django.urls import path
from .views import TelegramWebhookView, TelegramAuthView

app_name = 'telegram_auth'

urlpatterns = [
    path('telegram/', TelegramAuthView.as_view(), name='login'),
    path('telegram/webhook/', TelegramWebhookView.as_view(), name='webhook'),
]