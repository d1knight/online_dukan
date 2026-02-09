from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .models import Product, Category, Review
from .serializers import ProductSerializer, CategorySerializer, ReviewSerializer
from .filters import ProductFilter, CategoryFilter
from .pagination import CustomPagination


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all().order_by('id')
    serializer_class = CategorySerializer
    pagination_class = None 
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_class = CategoryFilter
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if 'parent' not in self.request.query_params and 'parent_name' not in self.request.query_params:
            queryset = queryset.filter(parent__isnull=True)
        return queryset


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

    @extend_schema(
        responses={200: ReviewSerializer(many=True)},
        description='Получить все отзывы о товаре',
        summary='Отзывы о товаре'
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

    @extend_schema(
        request={
            'type': 'object',
            'properties': {
                'rating': {'type': 'integer', 'minimum': 1, 'maximum': 5, 'nullable': True},
                'comment': {'type': 'string', 'nullable': True}
            }
        },
        responses={
            201: {'type': 'object', 'properties': {'status': {'type': 'string'}}},
            200: {'type': 'object', 'properties': {'status': {'type': 'string'}}}
        },
        examples=[
            OpenApiExample(
                'Отзыв с рейтингом и комментарием',
                value={
                    'rating': 5,
                    'comment': 'Отличный товар!'
                },
                request_only=True
            ),
            OpenApiExample(
                'Только рейтинг',
                value={
                    'rating': 4
                },
                request_only=True
            ),
            OpenApiExample(
                'Только комментарий',
                value={
                    'comment': 'Хороший товар, но есть минусы'
                },
                request_only=True
            )
        ],
        description='Добавить или обновить отзыв о товаре',
        summary='Добавить отзыв'
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated], url_path='add_review')
    def add_review(self, request, pk=None):
        from orders.models import OrderItem
        
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

    @extend_schema(
        responses={200: {'type': 'object', 'properties': {'status': {'type': 'string'}, 'message': {'type': 'string'}}}},
        description='Активировать/деактивировать товар (только для администратора)',
        summary='Переключить активность товара'
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def toggle_active(self, request, pk=None):
        product = self.get_object()
        product.is_active = not product.is_active
        product.save()
        status_msg = "Aktivlestirildi" if product.is_active else "Jasırıldı"
        return Response({'status': 'success', 'message': f'Tovar {status_msg}'})