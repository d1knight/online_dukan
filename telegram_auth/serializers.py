from rest_framework import serializers
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


class TelegramLoginSerializer(serializers.Serializer):
    code = serializers.CharField(
        max_length=6, 
        required=True,
        help_text='6-значный код из Telegram бота',
        style={'placeholder': '123456'}
    )

    def validate(self, data):
        code = data.get('code')
        if not code or len(code) != 6 or not code.isdigit():
            raise serializers.ValidationError("Kod 6 san bolıwı kerek")

        user = User.objects.filter(
            verification_code=code, 
            code_expires_at__gt=timezone.now()
        ).first()
        
        if not user:
            raise serializers.ValidationError("Kod qate yamasa waqtı ótken")

        return {'user': user}