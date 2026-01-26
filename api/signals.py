from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from .models import User, Cart  # <-- Импортируем Cart

# Сигнал для отправки Email (ваш старый код)
@receiver(post_save, sender=User)
def send_welcome_email(sender, instance, created, **kwargs):
    if created:
        print(f"--- EMAIL SENT TO {instance.email} ---")
        send_mail(
            'Xosh keldińiz!',
            f'Sálem {instance.username}, Online Dúkanǵa xosh keldińiz!',
            'admin@dukan.uz',
            [instance.email or 'test@example.com'],
            fail_silently=True,
        )

# --- НОВЫЙ КОД: Автоматическое создание корзины ---
@receiver(post_save, sender=User)
def create_user_cart(sender, instance, created, **kwargs):
    if created:
        Cart.objects.create(user=instance)
        print(f"--- CART CREATED FOR USER: {instance.username} ---")