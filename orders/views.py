from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from .models import Order, OrderItem
from .serializers import OrderSerializer, CheckoutSerializer
from cart.models import Cart
from products.pagination import CustomPagination

class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """Просмотр своих заказов — только для авторизованных"""
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')

class CheckoutView(APIView):
    """Оформление заказа — только для авторизованных"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        selected_ids = serializer.validated_data.get('selected_cart_items')
        address = serializer.validated_data.get('address', user.address)
        
        cart, _ = Cart.objects.get_or_create(user=user)
        items_to_buy = cart.items.select_related('product').filter(id__in=selected_ids)
        
        if not items_to_buy.exists(): 
            return Response({"error": "Tovar tańlanbadi"}, status=400)
        
        try:
            with transaction.atomic():
                total = 0
                prepared_items = []
                for item in items_to_buy:
                    if item.product.stock < item.quantity: 
                        raise ValueError(f"'{item.product.name}' jetkiliksiz (stokta: {item.product.stock})")
                    
                    price = item.product.discount_price or item.product.price
                    total += price * item.quantity
                    prepared_items.append({'item': item, 'price': price})
                
                order = Order.objects.create(user=user, total_price=total, address=address)
                for data in prepared_items:
                    item = data['item']
                    OrderItem.objects.create(
                        order=order, product=item.product, 
                        price=data['price'], quantity=item.quantity
                    )
                    item.product.stock -= item.quantity
                    item.product.save()
                
                items_to_buy.delete()
                return Response({
                    "status": "Buyırtpa qabıllandı", 
                    "order_id": order.id, 
                    "total_price": str(total)
                }, status=201)
        except ValueError as e: 
            return Response({"error": str(e)}, status=400)