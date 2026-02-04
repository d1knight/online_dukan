from rest_framework import serializers
from django.utils import timezone
from django.db.models import Avg
from .models import *

# --- User Profile ---
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'phone', 'address']
        read_only_fields = ['username', 'phone']

# --- Category ---
class CategorySerializer(serializers.ModelSerializer):
    class Meta: model = Category; fields = '__all__'

# --- Review ---
class ReviewSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    class Meta: 
        model = Review
        fields = ['id', 'username', 'rating', 'comment', 'created_at']
        extra_kwargs = {'comment': {'required': False}}

# --- Product ---
class ProductSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    avg_rating = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = '__all__'

    def get_avg_rating(self, obj):
        avg = obj.reviews.filter(rating__isnull=False).aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else 0

    def get_reviews_count(self, obj):
        return obj.reviews.count()

# --- Cart Item ---
class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), source='product', write_only=True)
    class Meta: model = CartItem; fields = ['id', 'product', 'product_id', 'quantity']

# --- Cart (Main) ---
class CartSerializer(serializers.ModelSerializer):
    cart_items = CartItemSerializer(source='items', many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'user', 'cart_items', 'total_price']

    def get_total_price(self, obj):
        total = 0
        for item in obj.items.all():
            price = item.product.discount_price if item.product.discount_price else item.product.price
            total += price * item.quantity
        return total

# --- Cart Add (Special for Swagger/Validation) ---
class CartAddSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=True, help_text="ID товара")
    quantity = serializers.IntegerField(required=False, default=1, min_value=1, help_text="Количество")

# --- Order ---
class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    class Meta: model = OrderItem; fields = ['product_name', 'price', 'quantity']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    class Meta: model = Order; fields = '__all__'

# --- Checkout ---
class CheckoutSerializer(serializers.Serializer):
    address = serializers.CharField(required=False)
    # Принимаем ID элементов корзины
    selected_cart_items = serializers.ListField(
        child=serializers.IntegerField(), 
        write_only=True, 
        required=True,
        help_text="ID элементов корзины (cart_item_id)"
    )

# --- Telegram Login ---
class TelegramLoginSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6, required=True)

    def validate(self, data):
        code = data.get('code')
        if not code or len(code) != 6 or not code.isdigit():
            raise serializers.ValidationError("Kod 6 san bolıwı kerek")

        user = User.objects.filter(verification_code=code, code_expires_at__gt=timezone.now()).first()
        if not user:
            raise serializers.ValidationError("Kod qate yamasa waqtı ótken")

        return {'user': user}