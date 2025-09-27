from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from reviews.models import (
    EMAIL_MAX_LENGTH, USERNAME_MAX_LENGTH, Category, Comment, Genre, Review,
    Title, User
)
from reviews.validators import username_validator


class TokenSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=USERNAME_MAX_LENGTH,
        required=True
    )
    confirmation_code = serializers.CharField(required=True)


class SignUpSerializer(serializers.Serializer):
    """Сериализатор для получение кода подтверждения."""

    email = serializers.EmailField(max_length=EMAIL_MAX_LENGTH, required=True)
    username = serializers.CharField(
        max_length=USERNAME_MAX_LENGTH,
        required=True
    )

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
    rating = serializers.IntegerField(source='_avg_score', read_only=True)

    class Meta:
        model = Title
        fields = (
            'id', 'name', 'year', 'rating', 'description', 'genre', 'category'
        )
        read_only_fields = ('id', 'name', 'year', 'rating', 'description',)


class TitleWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с произмевениями (запись)."""

    genre = serializers.SlugRelatedField(
        queryset=Genre.objects.all(), slug_field='slug', many=True
    )
    category = serializers.SlugRelatedField(
        queryset=Category.objects.all(), slug_field='slug'
    )

    class Meta:
        model = Title
        fields = ('id', 'name', 'year', 'description', 'genre', 'category')


class ReviewSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с отзывами."""

    author = serializers.ReadOnlyField(source='author.username')
    score = serializers.IntegerField(min_value=1, max_value=10)
    pub_date = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = Review
        fields = ('id', 'text', 'author', 'score', 'pub_date')

    def validate(self, attrs):
        request = self.context['request']
        title_id = self.context['view'].kwargs['title_id']

        if request.method == 'PATCH':
            return attrs

        if Review.objects.filter(
                title_id=title_id, author=request.user
        ).exists():
            raise ValidationError(
                'Вы уже оставляли отзыв на это произведение.'
            )

        return attrs


class CommentSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с коментариями."""

    author = serializers.ReadOnlyField(source='author.username')
    pub_date = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = Comment
        fields = ('id', 'text', 'author', 'pub_date')
        read_only_fields = ('id', 'author', 'pub_date')
