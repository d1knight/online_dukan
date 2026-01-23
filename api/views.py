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

# 1. Avtorizaciya
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

# 2. Onimler
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name']
    ordering_fields = ['price']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

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

# 3. Sebet (Cart)
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

    @action(detail=False, methods=['delete'], url_path='remove/(?P<product_id>\d+)')
    def remove(self, request, product_id=None):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        CartItem.objects.filter(cart=cart, product_id=product_id).delete()
        return Response({"status": "Removed"})

# 4. Checkout (Buyirtpa beriw)
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
            return Response({"error": "Tańlanǵan tawarlar sebetten tabılmadı."}, status=400)
        
        try:
            with transaction.atomic():
                total = 0
                for item in items_to_buy:
                    if item.product.stock < item.quantity:
                        raise ValueError(f"{item.product.name} qoymada jetkiliksiz!")
                    total += item.product.price * item.quantity
                
                order = Order.objects.create(user=user, total_price=total, address=address)
                
                for item in items_to_buy:
                    OrderItem.objects.create(
                        order=order, 
                        product=item.product, 
                        price=item.product.price, 
                        quantity=item.quantity
                    )
                    item.product.stock -= item.quantity
                    item.product.save()
                
                items_to_buy.delete()
                
                return Response({
                    "status": "Success", 
                    "order_id": order.id,
                    "message": "Buyırtpa rásmiylestirildi."
                }, status=201)

        except ValueError as e:
            return Response({"error": str(e)}, status=400)
        except Exception as e:
            return Response({"error": "Server qáteligi", "details": str(e)}, status=500)

# 5. Orders History
class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)