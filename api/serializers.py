from rest_framework import serializers
from .models import *

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ('username', 'password', 'first_name', 'phone', 'address')
    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

class CategorySerializer(serializers.ModelSerializer):
    class Meta: model = Category; fields = '__all__'

# Review Serializer отзыв
class ReviewSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    class Meta:
        model = Review
        fields = ['id', 'username', 'rating', 'comment', 'created_at']

class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True) # Nested Serializer
    category_id = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), source='category', write_only=True)
    reviews = ReviewSerializer(many=True, read_only=True) # Отзывты корсетемиз
    
    class Meta: model = Product; fields = '__all__'

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), source='product', write_only=True)
    class Meta: model = CartItem; fields = ['id', 'product', 'product_id', 'quantity']

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name')
    class Meta: model = OrderItem; fields = ['product_name', 'price', 'quantity']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    class Meta: model = Order; fields = '__all__'