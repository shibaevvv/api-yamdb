import re

from rest_framework import serializers

from users.models import User


class TokenSerializer(serializers.ModelSerializer):
    """Сериализатор для JWT-токена"""

    class Meta:
        model = User
        fields = ('username', 'confirmation_code')


class SignUpSerializer(serializers.Serializer):
    """Сериализатор для получение кода подтверждения."""

    email = serializers.EmailField(max_length=254, required=True)
    username = serializers.CharField(max_length=150, required=True)

    def validate_username(self, username):   
        if username == 'me':
            raise serializers.ValidationError(
                'Недопустимое имя пользователя!'
            )
        if not re.match(r'^[\w.@+-]+\Z', username):
            raise serializers.ValidationError(
                ('Имя пользователя может содержать латиницу, '
                 'цифры и знаки @ / . / + / - / _')
            )
        return username
