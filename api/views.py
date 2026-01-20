from rest_framework import viewsets, filters, generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema

from .models import *
from .serializers import *
from .filters import ProductFilter

# 1. Авторизация
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

#  Продукты
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter # Фильтр min_price, max_price
    search_fields = ['name']
    ordering_fields = ['price']

    # Админ может все, остальные только смотреть
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    # Добавить отзыв (POST /products/{id}/review/)
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def review(self, request, pk=None):
        product = self.get_object()
        Review.objects.create(
            user=request.user,
            product=product,
            rating=request.data.get('rating'),
            comment=request.data.get('comment')
        )
        return Response({'status': 'Review added'})

# Корзина
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
        except Product.DoesNotExist: return Response({"error": "No product"}, status=404)
        
        if product.stock < qty: return Response({"error": "No stock"}, status=400)
        
        cart, _ = Cart.objects.get_or_create(user=request.user)
        item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created: item.quantity += qty
        else: item.quantity = qty
        item.save()
        return Response({"status": "Added"})

    # Удаление (DELETE /cart/remove/{id}/)
    @action(detail=False, methods=['delete'], url_path='remove/(?P<product_id>\d+)')
    def remove(self, request, product_id=None):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        CartItem.objects.filter(cart=cart, product_id=product_id).delete()
        return Response({"status": "Removed"})

# Подверждение
class CheckoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(request_body=OrderSerializer)
    def post(self, request):
        user = request.user
        cart, _ = Cart.objects.get_or_create(user=user)
        items = cart.items.all()
        if not items: return Response({"error": "Empty cart"}, 400)
        
        total = 0
        for item in items:
            if item.product.stock < item.quantity:
                return Response({"error": f"{item.product.name} out of stock"}, 400)
            total += item.product.price * item.quantity
            
        order = Order.objects.create(user=user, total_price=total, address=request.data.get('address', user.address))
        
        for item in items:
            OrderItem.objects.create(order=order, product=item.product, price=item.product.price, quantity=item.quantity)
            item.product.stock -= item.quantity
            item.product.save()
            
        items.delete()
        return Response({"status": "Success", "order_id": order.id}, status=201)

# 5. Orders
class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)