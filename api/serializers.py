from rest_framework import serializers
from django.utils import timezone
from .models import *


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'phone', 'address']
        read_only_fields = ['username', 'phone']

class CategorySerializer(serializers.ModelSerializer):
    class Meta: model = Category; fields = '__all__'

class ReviewSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    class Meta: model = Review; fields = ['id', 'username', 'rating', 'comment', 'created_at']

class ProductSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    class Meta: model = Product; fields = '__all__'

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), source='product', write_only=True)
    class Meta: model = CartItem; fields = ['id', 'product', 'product_id', 'quantity']

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    class Meta: model = OrderItem; fields = ['product_name', 'price', 'quantity']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    class Meta: model = Order; fields = '__all__'

class CheckoutSerializer(serializers.Serializer):
    address = serializers.CharField(required=False)
    selected_products = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=True)

class TelegramLoginSerializer(serializers.Serializer):
    phone = serializers.CharField(required=False, allow_blank=True, default=None)
    code = serializers.CharField(max_length=6, required=True)

    def validate(self, data):
        code = data.get('code'); phone = data.get('phone')
        if not code or len(code) != 6 or not code.isdigit(): raise serializers.ValidationError("Kod 6 san bolıwı kerek")
        if phone:
            phone = phone.strip()
            if not phone.startswith('+'): phone = '+' + phone
            try: user = User.objects.get(phone=phone)
            except User.DoesNotExist: raise serializers.ValidationError("Paydalanıwshı tabılmadı")
        else:
            user = User.objects.filter(verification_code=code, code_expires_at__gt=timezone.now()).first()
            if not user: raise serializers.ValidationError("Kod qate yamasa waqtı ótken")
        if user.code_expires_at and user.code_expires_at < timezone.now(): raise serializers.ValidationError("Kod waqtı ótti")
        if user.verification_code != code: raise serializers.ValidationError("Kod qate")
        return {'user': user}