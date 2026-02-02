from django.contrib import admin
from .models import *

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'is_active')
    # фильтрлар
    list_filter = ('category', 'is_active')
    search_fields = ('name',)
    # Автозаполнение слага
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_active', 'stock', 'price')

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_price', 'status', 'created_at')
    list_filter = ('status',)
    inlines = [OrderItemInline]

admin.site.register([User, Cart, Review])