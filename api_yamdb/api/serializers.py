from rest_framework import serializers

from api.validators import username_validator
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
        return username_validator(username)


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для модели пользователя."""

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name', 'last_name', 'bio', 'role')

    def validate_username(self, username):
        return username_validator(username)


class SelfEditUserSerializer(UserSerializer):
    """Сериализатор для работы со своей учетной записью."""

    class Meta(UserSerializer.Meta):
        read_only_fields = ('role',)
