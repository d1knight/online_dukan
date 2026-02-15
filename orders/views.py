from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from drf_spectacular.utils import extend_schema #  документация ушын
from .models import Order, OrderItem
from .serializers import OrderSerializer, CheckoutSerializer
from cart.models import Cart
from products.pagination import CustomPagination
from rest_framework.throttling import ScopedRateThrottle


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')

    @extend_schema(
        request=None,
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'status': {'type': 'string'},
                    'message': {'type': 'string'},
                    'order_id': {'type': 'integer'}
                }
            }
        },
        description="Имитация оплаты заказа. Тело запроса не требуется. Статус меняется на 'paid' (Tólendi).",
        summary="Оплатить заказ"
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def pay(self, request, pk=None):
        """
        Имитация оплаты заказа. 
        Переводит статус из 'pending' в 'paid'.
        """
        order = self.get_object()
        
        if order.status != 'pending':
            return Response(
                {"error": "Bul buyırtpa aldın tólengen yamasa biykar etilgen"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Fake пулды толеу имитация
        order.status = 'paid'
        order.save()
        
        return Response({
            "status": "Tólendi",
            "message": "Buyırtpa ushın tólem qabıllandı. Endi pikir qaldıra alasız.",
            "order_id": order.id
        }, status=status.HTTP_200_OK)


class CheckoutView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'burst'
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        request=CheckoutSerializer,
        responses={201: {'type': 'object', 'properties': {'order_id': {'type': 'integer'}}}},
        description="Оформить заказ из товаров в корзине. После оформления нужно вызвать /pay/ для оплаты.",
        summary="Оформить заказ"
    )
    
    
    def post(self, request):
        # Десериализуем и валидируем входные данные
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # текущий пайдаланыушы
        user = request.user
        # Кайсы товарлар себетке салынды сатып алыу ушын
        selected_ids = serializer.validated_data.get('selected_cart_items')
    # Адрес доставки — корсеткенин аламыз, болмаса профильден аламыз
        address = serializer.validated_data.get('address', user.address)
        
        # Корзинаны аламыз жок болса жаратамыз
        cart, _ = Cart.objects.get_or_create(user=user)
        
        # тек сайланган товарларды аламыз (select_related аркалаы оптимизация кылынган)
        items_to_buy = cart.items.select_related('product').filter(id__in=selected_ids)
        
        # Егер еш зат сайланбаган болса ошибка сообщение кайтарады
        if not items_to_buy.exists():
            return Response({"error": "Tovar tańlanbadi"}, status=400)
        
        try:
            # Атомарная транзакция — хамме операция исленип шыгады я болмса улыма исленбейди 1 истемей калса
            with transaction.atomic():
                total = 0
                prepared_items = []   # будем хранить данные для создания OrderItem
                
                # Товардын бар жоклыгын тексерип суммасын есаплаймыз
                for item in items_to_buy:
                    if item.product.stock < item.quantity:
                        # Товар жок болса или аз болса смс жиюемиз
                        raise ValueError(f"'{item.product.name}' jetkiliksiz")
                    
                    # акционную цена болса аламыз, болмаса, куры priceдын озин аламыз
                    price = item.product.discount_price or item.product.price
                    total += price * item.quantity
                    
                    prepared_items.append({'item': item, 'price': price})
                
                # Заказды жаратамыз (статус  — pending болады басында)
                order = Order.objects.create(
                    user=user,
                    total_price=total,
                    address=address
                )
                
                # Заказдын позициясын жаратамыз хам онын калдыгын азайтамыз складтан
                for data in prepared_items:
                    item = data['item']
                    
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        price=data['price'],
                        quantity=item.quantity
                    )
                    
                    # Складтан аламыз - item.quantity
                    item.product.stock -= item.quantity
                    item.product.save() # саклаймыз склад озгерислерин
                
                # Сатып алган товарларды оширип тастаймыз
                items_to_buy.delete()
                
                # Жуап succes    болса
                return Response({
                    "status": "Buyırtpa jaratıldı",
                    "order_id": order.id,
                    "total_price": str(total),
                    "instruction": f"Endi buyırtpanı tólew ushın /api/orders/{order.id}/pay/ endpoyntına POST soraw jiberiń."
                }, status=201)
                
        except ValueError as e:
            # Ошибка товар жетпеди
            return Response({"error": str(e)}, status=400)