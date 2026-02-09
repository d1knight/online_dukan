import django_filters
from .models import Product, Category


class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr='lte')
    
    class Meta:
        model = Product
        fields = ['category', 'min_price', 'max_price']


class CategoryFilter(django_filters.FilterSet):
    parent = django_filters.NumberFilter(field_name="parent", lookup_expr='exact')
    parent_name = django_filters.CharFilter(method='filter_by_parent_name')
    
    def filter_by_parent_name(self, queryset, name, value):
        parent_category = Category.objects.filter(name__iexact=value).first()
        if parent_category:
            return queryset.filter(parent=parent_category)
        return queryset.none()
    
    class Meta:
        model = Category
        fields = ['parent', 'parent_name']