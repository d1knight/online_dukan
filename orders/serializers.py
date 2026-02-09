from rest_framework import serializers
from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta: 
        model = OrderItem
        fields = ['product_name', 'price', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta: 
        model = Order
        fields = '__all__'


class CheckoutSerializer(serializers.Serializer):
    address = serializers.CharField(required=False)
    selected_cart_items = serializers.ListField(
        child=serializers.IntegerField(), 
        write_only=True, 
        required=True
    )