from rest_framework import viewsets, permissions, filters, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from .models import Product, Category, Review
from .serializers import (
    ProductSerializer, 
    CategorySerializer, 
    ReviewSerializer, 
    AddReviewSerializer
)
from .filters import ProductFilter, CategoryFilter
from .pagination import CustomPagination

class CategoryViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Category.objects.all().order_by('id')
    serializer_class = CategorySerializer
    pagination_class = None 
    permission_classes = [permissions.AllowAny] # Просмотр категорий доступен всем
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

    def get_permissions(self):
        # 1. Добавление, удаление и редактирование товара — только Админ
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'toggle_active']:
            return [permissions.IsAdminUser()]
        # 2. Добавление отзыва — только авторизованный клиент
        if self.action == 'add_review':
            return [permissions.IsAuthenticated()]
        # 3. Просмотр списка товаров и одного товара — всем (AllowAny)
        return [permissions.AllowAny()]

    def get_queryset(self):
        # Админ видит все, клиенты — только активные товары
        if self.request.user.is_staff:
            return Product.objects.all().order_by('-id')
        return Product.objects.filter(is_active=True).order_by('-id')

    @extend_schema(
        request=AddReviewSerializer,
        responses={201: {'type': 'object', 'properties': {'status': {'type': 'string'}}}},
        description='Добавить/обновить отзыв. Доступно только после покупки товара.',
        summary='Добавить отзыв'
    )
    @action(detail=True, methods=['post'], url_path='add_review')
    def add_review(self, request, pk=None):
        from orders.models import OrderItem
        product = self.get_object()
        user = request.user
        
        serializer = AddReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Проверка покупки (клиент должен был купить этот товар ранее)
        if not OrderItem.objects.filter(order__user=user, product=product).exists():
            return Response({"error": "Pikir qaldırıw ushın aldın satıp alıń"}, status=403)

        defaults = {
            'rating': serializer.validated_data.get('rating'),
            'comment': serializer.validated_data.get('comment')
        }
        # Убираем None значения, чтобы не затереть существующие данные при частичном обновлении
        defaults = {k: v for k, v in defaults.items() if v is not None}

        review, created = Review.objects.update_or_create(
            user=user, product=product,
            defaults=defaults
        )
        msg = "Pikir qosıldı!" if created else "Pikir jańalandı!"
        return Response({'status': msg}, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny])
    def reviews(self, request, pk=None):
        product = self.get_object()
        reviews = product.reviews.all().order_by('-created_at')
        page = self.paginate_queryset(reviews)
        if page is not None:
            serializer = ReviewSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response(ReviewSerializer(reviews, many=True).data)

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        product = self.get_object()
        product.is_active = not product.is_active
        product.save()
        return Response({'status': 'success', 'message': f'Tovar {"Aktivlestirildi" if product.is_active else "Jasırıldı"}'})