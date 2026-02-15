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
from drf_spectacular.utils import extend_schema
from .serializers import TelegramLoginSerializer
from rest_framework.throttling import ScopedRateThrottle
from .utils import send_telegram_message

User = get_user_model()

# 26.01.2026 Telegram регистрация хам авторизация кылыу
@method_decorator(csrf_exempt, name='dispatch')
class TelegramWebhookView(APIView):
    permission_classes = [permissions.AllowAny] # хаммеге запрос жибериуге доступ беремиз
    
    def post(self, request):
        try: 
            data = json.loads(request.body) #Телеграм JSON жибереди
        except: 
            return Response(status=status.HTTP_200_OK)
            
        message = data.get('message', {}) #messageга келген объекты саклап аламыз
        if not message: 
            return Response(status=status.HTTP_200_OK) # жок болсада 200 кайтарып откерип жиберемиз тазасы болмаса
            # баска функция ислеуы ушын
            
        # саклап аламыз данныйларды    
        chat_id = message.get('chat', {}).get('id')
        text = message.get('text', '')
        contact = message.get('contact')
        
        from_user = message.get('from', {})
        first_name = from_user.get('first_name', '') or ""
        last_name = from_user.get('last_name', '') or ""
        tg_username = from_user.get('username')

        if not chat_id: #болмасада кейинги функция ислеуы ушын откерип жиберемиз статус 200 кылып
            return Response(status=status.HTTP_200_OK)

        if text == '/start': #егер старт басылса контактынызды жиберин кнопкасы шыгады
            keyboard = {
                "keyboard": [[{"text": "📱 Kontaktin'izdi jiberin'", "request_contact": True}]], 
                "resize_keyboard": True, 
                "one_time_keyboard": True
            }
            # стартты басса усынжай сообщениени жибереди бот телеграмга
            msg = f"Salem {first_name} 👋\nOnline Dúkan'ǵa xosh kelibsiz!\n⬇️ Kontaktti jiberin'"
            # кнопканы басып контакты жиберинды басса utilsдагы функцияны иске тусиремиз
            send_telegram_message(chat_id, msg, reply_markup=keyboard)
        
        # user телефон номерин жибергеннен кейнен    
        elif contact:
            phone = contact.get('phone_number') # телефон номерин аламыз
            if not phone.startswith('+'): # басында + болмаса косамыз
                phone = '+' + phone
            
            #усы жерде регистрация болады егер алдын исленбеген болса, егер исленген болса авторизация болады тек    
            user, created = User.objects.get_or_create(
                phone=phone, 
                defaults={'telegram_chat_id': str(chat_id)}
            )
            
            changed = False
            # Озрис болсын болмасын данныйларды озгертип шыгамыз
            
            # chat_id озгерген болса оны обновить кыламыз
            if user.telegram_chat_id != str(chat_id): 
                user.telegram_chat_id = str(chat_id)
                changed = True
            # аты озгерген болса кайтадан обновить кыламыз
            if user.first_name != first_name: 
                user.first_name = first_name
                changed = True
            # фамилиясыч озгерген болса кайтадан обновить кыламыз    
            if user.last_name != last_name: 
                user.last_name = last_name
                changed = True
            
            # username жаратамыз тгдан аты болса аты болады я болмаса фамилия кыламыз
            new_username = tg_username if tg_username else first_name
            if not new_username: 
                new_username = phone
            if user.username != new_username:
                if not User.objects.filter(username=new_username).exclude(id=user.id).exists(): 
                    user.username = new_username
                    changed = True
            
            # егер бир зат озгерген болса сохранить етемиз
            if changed: 
                user.save()

            if created: 
                send_telegram_message(chat_id, "🎉 <b>Siz tabıslı dizimnen óttińiz!</b>")
            else: 
                send_telegram_message(chat_id, "👋 <b>Qaytqanın'izdan quwanıshlımız!</b>")
            self.send_otp(user, chat_id)
        
        # егер пайдаланыушы логинды басса    
        elif text == '/login':
            try: 
                user = User.objects.get(telegram_chat_id=str(chat_id)) # userdi chat_id менен излеймиз
                self.send_otp(user, chat_id) #кейнен усы методы шакырамыз код алыуга
            except User.DoesNotExist: 
                send_telegram_message(chat_id, "/start basıń.") # изге стартка кайтарамыз
                
        return Response(status=status.HTTP_200_OK)
    
# 02/02/2026 озгерис болыд
    def send_otp(self, user, chat_id):
        code = str(random.randint(100000, 999999)) # код генерация кылып аламыз
        user.verification_code = code # userдын код полесына саклап коямыз
        user.code_expires_at = timezone.now() + timedelta(minutes=5) # кайсы уакытка шекем действовать екен билиу ушын
        user.save(update_fields=['verification_code', 'code_expires_at']) #саклаймыз базада
        msg = f"🔒 Code: <code>{code}</code>\n\n🔑 Jan'adan kod aliw ushin /login"
        send_telegram_message(chat_id, msg, reply_markup={"remove_keyboard": True})

#27.01.2026

# авторизация / кодты жиберип токен алыу ушын
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
        serializer = TelegramLoginSerializer(data=request.data) #сериализаторга жиберемиз тексериу ушын
        # егер кате болса ошибка шыгады кате или уакыт отти
        if not serializer.is_valid(): 
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        user = serializer.validated_data['user']
        # кодларды оширемиз валидациядан откеннен кейнен
        user.verification_code = None
        user.code_expires_at = None
        user.save(update_fields=['verification_code', 'code_expires_at'])
        
        refresh = RefreshToken.for_user(user) #токен пайда болады
        return Response({
            'refresh': str(refresh), 
            'access': str(refresh.access_token), 
            'username': user.username, 
            'role': user.role
        })