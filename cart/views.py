from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .models import Cart, CartItem
from products.models import Product
from .serializers import CartSerializer, CartAddSerializer


class CartViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        responses={200: CartSerializer},
        description='Получить содержимое корзины текущего пользователя',
        summary='Моя корзина'
    )
    def list(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    @extend_schema(
        request=CartAddSerializer,
        responses={200: {'type': 'object', 'properties': {'status': {'type': 'string'}}}},
        examples=[
            OpenApiExample(
                'Добавить 2 товара',
                value={
                    'product_id': 1,
                    'quantity': 2
                },
                request_only=True
            )
        ],
        description='Добавить товар в корзину',
        summary='Добавить в корзину'
    )
    @action(detail=False, methods=['post'])
    def add(self, request):
        serializer = CartAddSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        p_id = serializer.validated_data['product_id']
        qty = serializer.validated_data['quantity']

        if qty < 1: 
            return Response({"error": "Sanı 1 den kem bolmawı kerek"}, 400)

        try: 
            product = Product.objects.get(id=p_id)
        except Product.DoesNotExist: 
            return Response({"error": "Tovar tabılmadı"}, 404)
        
        if product.stock <= 0: 
            return Response({"error": "Qoymada joq"}, 400)
        if product.stock < qty: 
            return Response({"error": f"Jetkiliksiz. Qalǵanı: {product.stock}"}, 400)
        
        cart, _ = Cart.objects.get_or_create(user=request.user)
        item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created: 
            item.quantity += qty
        else: 
            item.quantity = qty
        item.save()
        return Response({"status": "Qosıldı"})

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='cart_item_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='ID элемента корзины'
            )
        ],
        responses={200: {'type': 'object', 'properties': {'status': {'type': 'string'}}}},
        description='Удалить товар из корзины',
        summary='Удалить из корзины'
    )
    @action(detail=False, methods=['delete'], url_path=r'remove/(?P<cart_item_id>\d+)')
    def remove(self, request, cart_item_id=None):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        item = CartItem.objects.filter(cart=cart, id=cart_item_id).first()
        if item:
            item.delete()
            return Response({"status": "Óshirildi"}, status=200)
        return Response({"error": "Tabılmadı"}, status=404)