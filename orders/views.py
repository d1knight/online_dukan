from django.db import transaction
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiExample
from .models import Order, OrderItem
from cart.models import Cart
from .serializers import OrderSerializer, CheckoutSerializer
from products.pagination import CustomPagination


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')


class CheckoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        request=CheckoutSerializer,
        responses={
            201: {
                'type': 'object',
                'properties': {
                    'status': {'type': 'string'},
                    'order_id': {'type': 'integer'},
                    'total_price': {'type': 'string'}
                }
            }
        },
        examples=[
            OpenApiExample(
                'Оформить заказ',
                value={
                    'address': 'г. Нукус, ул. Достлык 10, кв. 5',
                    'selected_cart_items': [1, 2, 3]
                },
                request_only=True
            )
        ],
        description='Оформить заказ из выбранных товаров корзины',
        summary='Оформить заказ'
    )
    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        if not serializer.is_valid(): 
            return Response(serializer.errors, status=400)

        user = request.user
        selected_cart_item_ids = serializer.validated_data.get('selected_cart_items')
        address = serializer.validated_data.get('address', user.address)
        
        cart, _ = Cart.objects.get_or_create(user=user)
        items_to_buy = cart.items.select_related('product').filter(id__in=selected_cart_item_ids)
        
        if not items_to_buy.exists(): 
            return Response({"error": "Tovar tańlanbadi"}, 400)
        
        try:
            with transaction.atomic():
                total = 0
                prepared_items = []
                for item in items_to_buy:
                    if item.product.stock <= 0: 
                        raise ValueError(f"'{item.product.name}' tawsıldı!")
                    if item.product.stock < item.quantity: 
                        raise ValueError(f"'{item.product.name}' jetkiliksiz.")
                    
                    price = item.product.discount_price if item.product.discount_price else item.product.price
                    total += price * item.quantity
                    prepared_items.append({'item': item, 'price': price})
                
                order = Order.objects.create(user=user, total_price=total, address=address)
                for data in prepared_items:
                    item = data['item']
                    OrderItem.objects.create(
                        order=order, 
                        product=item.product, 
                        price=data['price'], 
                        quantity=item.quantity
                    )
                    item.product.stock -= item.quantity
                    item.product.save()
                
                items_to_buy.delete()
                return Response({
                    "status": "Buyırtpa qabıllandı", 
                    "order_id": order.id, 
                    "total_price": str(total)
                }, 201)
        except ValueError as e: 
            return Response({"error": str(e)}, 400)