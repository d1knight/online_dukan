import json
import random
from datetime import timedelta
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema  # ДОБАВЬТЕ
from .serializers import TelegramLoginSerializer
from .utils import send_telegram_message

User = get_user_model()


@method_decorator(csrf_exempt, name='dispatch')
class TelegramWebhookView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        try: 
            data = json.loads(request.body)
        except: 
            return Response(status=status.HTTP_200_OK)
            
        message = data.get('message', {})
        if not message: 
            return Response(status=status.HTTP_200_OK)
            
        chat_id = message.get('chat', {}).get('id')
        text = message.get('text', '')
        contact = message.get('contact')
        
        from_user = message.get('from', {})
        first_name = from_user.get('first_name', '') or ""
        last_name = from_user.get('last_name', '') or ""
        tg_username = from_user.get('username')

        if not chat_id: 
            return Response(status=status.HTTP_200_OK)

        if text == '/start':
            keyboard = {
                "keyboard": [[{"text": "📱 Kontaktin'izdi jiberin'", "request_contact": True}]], 
                "resize_keyboard": True, 
                "one_time_keyboard": True
            }
            msg = f"Salem {first_name} 👋\nOnline Dúkan'ǵa xosh kelibsiz!\n⬇️ Kontaktti jiberin'"
            send_telegram_message(chat_id, msg, reply_markup=keyboard)
            
        elif contact:
            phone = contact.get('phone_number')
            if not phone.startswith('+'): 
                phone = '+' + phone
                
            user, created = User.objects.get_or_create(
                phone=phone, 
                defaults={'telegram_chat_id': str(chat_id)}
            )
            
            changed = False
            if user.telegram_chat_id != str(chat_id): 
                user.telegram_chat_id = str(chat_id)
                changed = True
            if user.first_name != first_name: 
                user.first_name = first_name
                changed = True
            if user.last_name != last_name: 
                user.last_name = last_name
                changed = True
            
            new_username = tg_username if tg_username else first_name
            if not new_username: 
                new_username = phone
            if user.username != new_username:
                if not User.objects.filter(username=new_username).exclude(id=user.id).exists(): 
                    user.username = new_username
                    changed = True
            
            if changed: 
                user.save()

            if created: 
                send_telegram_message(chat_id, "🎉 <b>Siz tabıslı dizimnen óttińiz!</b>")
            else: 
                send_telegram_message(chat_id, "👋 <b>Qaytqanın'izdan quwanıshlımız!</b>")
            self.send_otp(user, chat_id)
            
        elif text == '/login':
            try: 
                user = User.objects.get(telegram_chat_id=str(chat_id))
                self.send_otp(user, chat_id)
            except User.DoesNotExist: 
                send_telegram_message(chat_id, "/start basıń.")
                
        return Response(status=status.HTTP_200_OK)

    def send_otp(self, user, chat_id):
        code = str(random.randint(100000, 999999))
        user.verification_code = code
        user.code_expires_at = timezone.now() + timedelta(minutes=5)
        user.save(update_fields=['verification_code', 'code_expires_at'])
        msg = f"🔒 Code: <code>{code}</code>\n\n🔑 Jan'adan kod aliw ushin /login"
        send_telegram_message(chat_id, msg, reply_markup={"remove_keyboard": True})


class TelegramAuthView(APIView):
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        request=TelegramLoginSerializer,
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'refresh': {'type': 'string'},
                    'access': {'type': 'string'},
                    'username': {'type': 'string'},
                    'role': {'type': 'string'}
                }
            }
        },
        description='Авторизация с помощью кода из Telegram',
        summary='Telegram Login'
    )
    def post(self, request):
        serializer = TelegramLoginSerializer(data=request.data)
        if not serializer.is_valid(): 
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        user = serializer.validated_data['user']
        user.verification_code = None
        user.code_expires_at = None
        user.save(update_fields=['verification_code', 'code_expires_at'])
        
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh), 
            'access': str(refresh.access_token), 
            'username': user.username, 
            'role': user.role
        })