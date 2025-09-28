from django.conf import settings
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from reviews.models import (
    EMAIL_MAX_LENGTH, USERNAME_MAX_LENGTH, Category, Comment, Genre, Review,
    Title, User
)
from reviews.validators import username_validator

REVIEW_EXISTS_ERROR = 'Отзыв на произведение "{}" оставлен ранее.'


class TokenSignUpBaseSerializer(serializers.Serializer):
    """Базовый сериализатор для регистрации и получения JWT-токена."""

    username = serializers.CharField(
        max_length=USERNAME_MAX_LENGTH,
        required=True,
        validators=[username_validator,]
    )


class TokenSerializer(TokenSignUpBaseSerializer):
    """Сериализатор для получение JWT-токена."""

    confirmation_code = serializers.CharField(
        max_length=settings.CONFIRMATION_CODE_LENGTH,
        required=True
    )


class SignUpSerializer(TokenSignUpBaseSerializer):
    """Сериализатор для регистрации и получения кода подтверждения."""

    email = serializers.EmailField(max_length=EMAIL_MAX_LENGTH, required=True)


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


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор для работы с категориями."""

    class Meta:
        model = Category
        fields = ('name', 'slug')


class GenreSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с жанрами."""

    class Meta:
        model = Genre
        fields = ('name', 'slug')


class TitleReadSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с произмевениями (чтение)."""

    genre = GenreSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)
    rating = serializers.IntegerField(read_only=True)

    class Meta:
        model = Title
        fields = (
            'id', 'name', 'year', 'rating', 'description', 'genre', 'category'
        )
        read_only_fields = fields


class TitleWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с произмевениями (запись)."""

    genre = serializers.SlugRelatedField(
        queryset=Genre.objects.all(), slug_field='slug', many=True
    )
    category = serializers.SlugRelatedField(
        queryset=Category.objects.all(), slug_field='slug'
    )

    def to_representation(self, value):
        return TitleReadSerializer(value).data

    class Meta:
        model = Title
        fields = ('id', 'name', 'year', 'description', 'genre', 'category')


class ReviewSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с отзывами."""

    author = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username'
    )

    class Meta:
        model = Review
        fields = ('id', 'text', 'author', 'score', 'pub_date')

    def validate(self, attrs):
        request = self.context['request']
        if request.method == 'PATCH':
            return attrs
        title_id = self.context['view'].kwargs['title_id']
        if Review.objects.filter(
                title_id=title_id, author=request.user
        ).exists():
            raise ValidationError(
                REVIEW_EXISTS_ERROR.format(Title.objects.get(id=title_id).name)
            )
        return attrs


class CommentSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с коментариями."""

    author = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username'
    )

    class Meta:
        model = Comment
        fields = ('id', 'text', 'author', 'pub_date')
