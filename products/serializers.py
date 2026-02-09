from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Product, Category, Review

class CategorySerializer(serializers.ModelSerializer):
    class Meta: 
        model = Category
        fields = '__all__'

class ReviewSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta: 
        model = Review
        fields = ['id', 'username', 'rating', 'comment', 'created_at']
        extra_kwargs = {'comment': {'required': False}}

# НОВЫЙ СЕРИАЛИЗАТОР ДЛЯ SWAGGER И ВАЛИДАЦИИ
class AddReviewSerializer(serializers.Serializer):
    rating = serializers.IntegerField(
        min_value=1, 
        max_value=5, 
        required=False, 
        help_text="Оценка от 1 до 5"
    )
    comment = serializers.CharField(
        required=False, 
        allow_blank=True, 
        help_text="Текст отзыва"
    )

    def validate(self, attrs):
        if not attrs.get('rating') and not attrs.get('comment'):
            raise serializers.ValidationError("Нужно указать хотя бы оценку или комментарий.")
        return attrs

class ProductSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    
    @extend_schema_field(serializers.FloatField)
    def get_avg_rating(self, obj):
        from django.db.models import Avg
        avg = obj.reviews.filter(rating__isnull=False).aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else 0
    
    @extend_schema_field(serializers.IntegerField)
    def get_reviews_count(self, obj):
        return obj.reviews.count()
    
    avg_rating = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = '__all__'