import django_filters
from .models import Product, Category

# Onimler filtri (Sizde bar bolǵan)
class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr='lte')
    
    class Meta:
        model = Product
        fields = ['category', 'min_price', 'max_price']

# --- JAŃA: Kategoriya filtri ---
class CategoryFilter(django_filters.FilterSet):
    # Parent ID boyınsha filtrlew (Mısalı: ?parent=1)
    parent = django_filters.NumberFilter(field_name="parent", lookup_expr='exact')
    
    # Parent kategoriya atı boyınsha filtrlew (Mısalı: ?parent_name=Telephone)
    parent_name = django_filters.CharFilter(method='filter_by_parent_name')
    
    def filter_by_parent_name(self, queryset, name, value):
        """
        Родительской категории атı boyınsha filtrlew
        Mısal: ?parent_name=Electronics -> Electronics kategoriyasının balaların qaytaradı
        """
        # Aldı menen parent kategoriyani tabamız (case-insensitive)
        parent_category = Category.objects.filter(name__iexact=value).first()
        if parent_category:
            # Sonı onan balalarin qaytaramız
            return queryset.filter(parent=parent_category)
        # Eger tappe al'madı bolsa, bos tizim qaytaramız
        return queryset.none()
    
    class Meta:
        model = Category
        fields = ['parent', 'parent_name']