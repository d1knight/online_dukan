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
    # Parent boyınsha filtrlew (Mısalı: ?parent=null yamasa ?parent=1)
    # parent__isnull=True dep jiberiw ushın 'is_root' degen parametr qossaq boladı,
    # biraq standart 'parent' maydanı da jetkilikli.
    
    class Meta:
        model = Category
        fields = ['parent']