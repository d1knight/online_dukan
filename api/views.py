import json
import random
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import viewsets, generics, permissions, status, filters, mixins
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django_filters.rest_framework import DjangoFilterBackend

from .models import *
from .serializers import *
from .filters import ProductFilter, CategoryFilter
from .utils import send_telegram_message
from .pagination import CustomPagination

# 1. Profile
class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'patch']
    def get_object(self):
        return self.request.user

# 2. Categories
class CategoryViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Category.objects.all().order_by('id')
    serializer_class = CategorySerializer
    pagination_class = None 
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_class = CategoryFilter
    
    @swagger_auto_schema(
        operation_description="""
        Получить список категорий.
        
        **По умолчанию**: возвращаются только корневые (родительские) категории.
        
        **Фильтры**:
        - `parent` (ID) - получить дочерние категории по ID родителя
          Пример: `/api/categories/?parent=1`
        
        - `parent_name` (string) - получить дочерние категории по имени родителя
          Пример: `/api/categories/?parent_name=Telephone`
          Пример: `/api/categories/?parent_name=Electronics`
        """,
        manual_parameters=[
            openapi.Parameter(
                'parent',
                openapi.IN_QUERY,
                description="ID родительской категории для получения дочерних категорий",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
            openapi.Parameter(
                'parent_name',
                openapi.IN_QUERY,
                description="Имя родительской категории для получения дочерних категорий (например: Telephone, Electronics)",
                type=openapi.TYPE_STRING,
                required=False
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        По умолчанию возвращает только корневые категории (parent=null).
        Для получения дочерних категорий используйте фильтры:
        - ?parent=<id> - по ID родителя
        - ?parent_name=<name> - по имени родителя
        
        Примеры:
        - GET /api/categories/ -> только корневые категории
        - GET /api/categories/?parent=1 -> дочерние категории parent_id=1
        - GET /api/categories/?parent_name=Telephone -> дочерние категории родителя "Telephone"
        """
        queryset = super().get_queryset()
        # Если НИ ОДИН фильтр не указан, возвращаем только корневые категории
        if 'parent' not in self.request.query_params and 'parent_name' not in self.request.query_params:
            queryset = queryset.filter(parent__isnull=True)
        return queryset

# 3. Products
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name']
    ordering_fields = ['price']
    pagination_class = CustomPagination

    def get_queryset(self):
        if self.request.user.is_staff:
            return Product.objects.all().order_by('-id')
        return Product.objects.filter(is_active=True).order_by('-id')

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'toggle_active']:
            return [permissions.IsAdminUser()]
        if self.action in ['add_review']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    @swagger_auto_schema(
        operation_description="Получить отзывы товара",
        responses={200: ReviewSerializer(many=True)}
    )
    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny])
    def reviews(self, request, pk=None):
        product = self.get_object()
        reviews = product.reviews.all().order_by('-created_at')
        page = self.paginate_queryset(reviews)
        if page is not None:
            serializer = ReviewSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'rating': openapi.Schema(type=openapi.TYPE_INTEGER, description="1-5"), 
                'comment': openapi.Schema(type=openapi.TYPE_STRING)
            }
        )
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated], url_path='add_review')
    def add_review(self, request, pk=None):
        # Защита от анонимов
        if not request.user.is_authenticated:
            return Response({"error": "Avtorizatsiyadan o'tiń"}, status=status.HTTP_401_UNAUTHORIZED)

        product = self.get_object()
        user = request.user
        
        has_purchased = OrderItem.objects.filter(order__user=user, product=product).exists()
        if not has_purchased:
            return Response({"error": "Pikir qaldırıw ushın aldın satıp alıń"}, status=403)

        rating = request.data.get('rating')
        comment = request.data.get('comment')

        if not rating and not comment:
             return Response({"error": "Reyting yamasa kommentariy jazıwıńız kerek"}, status=400)

        if rating is not None:
            try:
                rating = int(rating)
                if not (1 <= rating <= 5): raise ValueError
            except (ValueError, TypeError):
                return Response({"error": "Reyting 1 hám 5 aralığında bolıwı kerek"}, status=400)

        defaults = {}
        if comment is not None: defaults['comment'] = comment
        if rating is not None: defaults['rating'] = rating

        review, created = Review.objects.update_or_create(
            user=user, product=product,
            defaults=defaults
        )
        msg = "Pikir qosıldı!" if created else "Pikir jańalandı!"
        return Response({'status': msg}, status=201 if created else 200)

    @swagger_auto_schema(auto_schema=None)
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def toggle_active(self, request, pk=None):
        product = self.get_object()
        product.is_active = not product.is_active
        product.save()
        status_msg = "Aktivlestirildi" if product.is_active else "Jasırıldı"
        return Response({'status': 'success', 'message': f'Tovar {status_msg}'})

# 4. Cart
class CartViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    # Pagination здесь не нужен для list, так как мы возвращаем один объект Cart

    @swagger_auto_schema(responses={200: CartSerializer()})
    def list(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        # Возвращаем корзину целиком (с total_price и cart_items)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    @swagger_auto_schema(
        request_body=CartAddSerializer, 
        responses={200: "Добавлено", 400: "Ошибка"}
    )
    @action(detail=False, methods=['post'])
    def add(self, request):
        # Используем отдельный сериализатор для валидации входных данных
        serializer = CartAddSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        p_id = serializer.validated_data['product_id']
        qty = serializer.validated_data['quantity']

        if qty < 1: return Response({"error": "Sanı 1 den kem bolmawı kerek"}, 400)

        try: product = Product.objects.get(id=p_id)
        except Product.DoesNotExist: return Response({"error": "Tovar tabılmadı"}, 404)
        
        if product.stock <= 0: return Response({"error": "Qoymada joq"}, 400)
        if product.stock < qty: return Response({"error": f"Jetkiliksiz. Qalǵanı: {product.stock}"}, 400)
        
        cart, _ = Cart.objects.get_or_create(user=request.user)
        item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created: item.quantity += qty
        else: item.quantity = qty
        item.save()
        return Response({"status": "Qosıldı"})

    @swagger_auto_schema(
        manual_parameters=[openapi.Parameter('cart_item_id', openapi.IN_PATH, description="ID элемента корзины", type=openapi.TYPE_INTEGER)]
    )
    @action(detail=False, methods=['delete'], url_path=r'remove/(?P<cart_item_id>\d+)')
    def remove(self, request, cart_item_id=None):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        item = CartItem.objects.filter(cart=cart, id=cart_item_id).first()
        if item:
            item.delete()
            return Response({"status": "Óshirildi"}, status=200)
        return Response({"error": "Tabılmadı"}, status=404)

# 5. Checkout
class CheckoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(request_body=CheckoutSerializer)
    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        if not serializer.is_valid(): return Response(serializer.errors, status=400)

        user = request.user
        selected_cart_item_ids = serializer.validated_data.get('selected_cart_items')
        address = serializer.validated_data.get('address', user.address)
        
        cart, _ = Cart.objects.get_or_create(user=user)
        # Фильтруем по ID элементов корзины
        items_to_buy = cart.items.select_related('product').filter(id__in=selected_cart_item_ids)
        
        if not items_to_buy.exists(): return Response({"error": "Tovar tańlanbadi"}, 400)
        
        try:
            with transaction.atomic():
                total = 0
                prepared_items = []
                for item in items_to_buy:
                    if item.product.stock <= 0: raise ValueError(f"'{item.product.name}' tawsıldı!")
                    if item.product.stock < item.quantity: raise ValueError(f"'{item.product.name}' jetkiliksiz.")
                    
                    price = item.product.discount_price if item.product.discount_price else item.product.price
                    total += price * item.quantity
                    prepared_items.append({'item': item, 'price': price})
                
                order = Order.objects.create(user=user, total_price=total, address=address)
                for data in prepared_items:
                    item = data['item']
                    OrderItem.objects.create(order=order, product=item.product, price=data['price'], quantity=item.quantity)
                    item.product.stock -= item.quantity
                    item.product.save()
                
                # Удаляем купленные элементы из корзины
                items_to_buy.delete()
                return Response({"status": "Buyırtpa qabıllandı", "order_id": order.id, "total_price": total}, 201)
        except ValueError as e: return Response({"error": str(e)}, 400)

# 6. Orders
class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')

# 7. Telegram
@method_decorator(csrf_exempt, name='dispatch')
class TelegramWebhookView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        try: data = json.loads(request.body)
        except: return Response(status=status.HTTP_200_OK)
        message = data.get('message', {})
        if not message: return Response(status=status.HTTP_200_OK)
        chat_id = message.get('chat', {}).get('id')
        text = message.get('text', '')
        contact = message.get('contact')
        
        from_user = message.get('from', {})
        first_name = from_user.get('first_name', '') or ""
        last_name = from_user.get('last_name', '') or ""
        tg_username = from_user.get('username')

        if not chat_id: return Response(status=status.HTTP_200_OK)

        if text == '/start':
            keyboard = {"keyboard": [[{"text": "📱 Kontaktin'izdi jiberin'", "request_contact": True}]], "resize_keyboard": True, "one_time_keyboard": True}
            msg = f"Salem {first_name} 👋\nOnline Dúkan'ǵa xosh kelibsiz!\n⬇️ Kontaktti jiberin'"
            send_telegram_message(chat_id, msg, reply_markup=keyboard)
        elif contact:
            phone = contact.get('phone_number')
            if not phone.startswith('+'): phone = '+' + phone
            user, created = User.objects.get_or_create(phone=phone, defaults={'telegram_chat_id': str(chat_id)})
            
            changed = False
            if user.telegram_chat_id != str(chat_id): user.telegram_chat_id = str(chat_id); changed = True
            if user.first_name != first_name: user.first_name = first_name; changed = True
            if user.last_name != last_name: user.last_name = last_name; changed = True
            
            new_username = tg_username if tg_username else first_name
            if not new_username: new_username = phone
            if user.username != new_username:
                if not User.objects.filter(username=new_username).exclude(id=user.id).exists(): user.username = new_username; changed = True
            
            if changed: user.save()

            if created: send_telegram_message(chat_id, "🎉 <b>Siz tabıslı dizimnen óttińiz!</b>")
            else: send_telegram_message(chat_id, "👋 <b>Qaytqanın'izdan quwanıshlımız!</b>")
            self.send_otp(user, chat_id)
        elif text == '/login':
            try: user = User.objects.get(telegram_chat_id=str(chat_id)); self.send_otp(user, chat_id)
            except User.DoesNotExist: send_telegram_message(chat_id, "/start basıń.")
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
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={'code': openapi.Schema(type=openapi.TYPE_STRING, example="123456")},
            required=['code'],
        )
    )
    def post(self, request):
        serializer = TelegramLoginSerializer(data=request.data)
        if not serializer.is_valid(): return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user = serializer.validated_data['user']
        user.verification_code = None; user.code_expires_at = None; user.save(update_fields=['verification_code', 'code_expires_at'])
        refresh = RefreshToken.for_user(user)
        return Response({'refresh': str(refresh), 'access': str(refresh.access_token), 'username': user.username, 'role': user.role})