from rest_framework import serializers
from .models import *

# 1. Registraciya
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('username', 'password', 'first_name', 'phone', 'address')
    
    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

# 2. Kategoriya
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

# 3. Review (Pikirler)
class ReviewSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Review
        fields = ['id', 'username', 'rating', 'comment', 'created_at']

# 4. Product (Onimler)
class ProductSerializer(serializers.ModelSerializer):
    # Kategoriya maǵlıwmatların tolıq kórsetiw
    category = CategorySerializer(read_only=True)
    # Onim qosqanda ID arqalı tańlaw ushın
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True
    )
    # Onimge tiyisli pikirlerdi kórsetiw
    reviews = ReviewSerializer(many=True, read_only=True)
    
    class Meta:
        model = Product
        fields = '__all__'

# 5. Cart Item (Sebet elementleri)
class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source='product', write_only=True
    )
    
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'quantity']

# 6. Order Item (Buyırtpa elementleri)
class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['product_name', 'price', 'quantity']

# 7. Order (Buyırtpa)
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = '__all__'

# 8. CHECKOUT SERIALIZER (Tańlap satıp alıw ushın)
class CheckoutSerializer(serializers.Serializer):
    address = serializers.CharField(required=False)
    # Paydalanıwshı satıp almaqshı bolǵan ónimlerdiń ID dizimi (Mısalı: [1, 5, 10])
    selected_products = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=True,
        help_text="Satıp alınatuǵın ónimlerdiń ID dizimi (Mısalı: [1, 5])"
    )