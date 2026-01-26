from rest_framework import viewsets, filters, generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from django.db import transaction

from .models import *
from .serializers import *
from .filters import ProductFilter

# 1. Регистрация
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

# 2. Товары
class ProductViewSet(viewsets.ModelViewSet):
    # Эта строка нужна для Router
    queryset = Product.objects.all() 
    
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name']
    ordering_fields = ['price']

    # --- ЛОГИКА ВИДИМОСТИ ТОВАРОВ ---
    def get_queryset(self):
        # Админ видит ВСЕ товары, Клиент — только АКТИВНЫЕ
        if self.request.user.is_staff:
            return Product.objects.all()
        return Product.objects.filter(is_active=True)

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'toggle_active']:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    # --- КНОПКА: Скрыть/Показать товар (Только для Админа) ---
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def toggle_active(self, request, pk=None):
        product = self.get_object()
        product.is_active = not product.is_active
        product.save()
        
        status_msg = "Активирован" if product.is_active else "Скрыт"
        return Response({
            'status': 'success',
            'product': product.name,
            'is_active': product.is_active,
            'message': f'Товар {status_msg}'
        })

    # --- Логика отзывов ---
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def review(self, request, pk=None):
        product = self.get_object()
        user = request.user

        if Review.objects.filter(user=user, product=product).exists():
             return Response({"error": "Вы уже оставили отзыв!"}, status=400)

        has_purchased = OrderItem.objects.filter(order__user=user, product=product).exists()
        if not has_purchased:
            return Response({"error": "Сначала купите товар"}, status=403)

        rating = request.data.get('rating')
        if not rating or int(rating) < 1 or int(rating) > 5:
             return Response({"error": "Рейтинг от 1 до 5"}, status=400)

        Review.objects.create(
            user=user,
            product=product,
            rating=rating,
            comment=request.data.get('comment', '')
        )
        return Response({'status': 'Отзыв добавлен!'}, status=201)

# 3. Корзина
class CartViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return Response(CartItemSerializer(cart.items.all(), many=True).data)

    @swagger_auto_schema(request_body=CartItemSerializer)
    @action(detail=False, methods=['post'])
    def add(self, request):
        p_id = request.data.get('product_id')
        qty = int(request.data.get('quantity', 1))
        
        try: product = Product.objects.get(id=p_id)
        except Product.DoesNotExist: return Response({"error": "Товар не найден"}, 404)
        
        # --- ПРОВЕРКА НАЛИЧИЯ ---
        if product.stock <= 0:
            return Response({"error": "Товара нет в наличии (Out of stock)"}, status=400)
        
        if product.stock < qty: 
            return Response({"error": f"Недостаточно товара. Доступно: {product.stock} шт."}, status=400)
        # ------------------------
        
        cart, _ = Cart.objects.get_or_create(user=request.user)
        item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created: item.quantity += qty
        else: item.quantity = qty
        item.save()
        return Response({"status": "Добавлено"})

    @action(detail=False, methods=['delete'], url_path='remove/(?P<product_id>\d+)')
    def remove(self, request, product_id=None):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        CartItem.objects.filter(cart=cart, product_id=product_id).delete()
        return Response({"status": "Удалено"})

# 4. Checkout (С учетом скидки)
class CheckoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(request_body=CheckoutSerializer)
    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        user = request.user
        selected_ids = serializer.validated_data.get('selected_products')
        address = serializer.validated_data.get('address', user.address)

        cart, _ = Cart.objects.get_or_create(user=user)
        items_to_buy = cart.items.select_related('product').filter(product_id__in=selected_ids)
        
        if not items_to_buy.exists():
            return Response({"error": "Товары не выбраны"}, 400)
        
        try:
            with transaction.atomic():
                total = 0
                # Список для хранения подготовленных товаров, чтобы не считать цену дважды
                prepared_items = []

                for item in items_to_buy:
                    # 1. Проверка наличия
                    if item.product.stock <= 0:
                        raise ValueError(f"Товар '{item.product.name}' закончился (Нет в наличии)!")
                    
                    if item.product.stock < item.quantity:
                        raise ValueError(f"Товара '{item.product.name}' недостаточно. Доступно: {item.product.stock}")
                    
                    # 2. ОПРЕДЕЛЕНИЕ ЦЕНЫ (Скидка или обычная)
                    if item.product.discount_price:
                        final_price = item.product.discount_price
                    else:
                        final_price = item.product.price

                    # 3. Расчет суммы
                    total += final_price * item.quantity
                    
                    # Сохраняем данные во временный список
                    prepared_items.append({
                        'item_obj': item,
                        'final_price': final_price
                    })
                
                # 4. Создание Заказа
                order = Order.objects.create(user=user, total_price=total, address=address)
                
                # 5. Создание позиций заказа и обновление склада
                for data in prepared_items:
                    item = data['item_obj']
                    price = data['final_price']

                    OrderItem.objects.create(
                        order=order, 
                        product=item.product, 
                        price=price, # Записываем ту цену, по которой фактически купили
                        quantity=item.quantity
                    )
                    item.product.stock -= item.quantity
                    item.product.save()
                
                items_to_buy.delete()
                
                return Response({
                    "status": "Заказ оформлен", 
                    "order_id": order.id,
                    "total_price": total
                }, 201)

        except ValueError as e:
            return Response({"error": str(e)}, 400)
        except Exception as e:
            return Response({"error": "Server error", "details": str(e)}, 500)

# 5. История заказов
class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)