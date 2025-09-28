import random

from django.conf import settings
from django.core.mail import send_mail
from django.db import IntegrityError
from django.db.models import Avg
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters
from rest_framework import (
    filters as drf_filters, status, viewsets, mixins
)
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken

from api.permissions import (IsAdminOnlyPermission, IsAdminOrReadOnly,
                             IsAuthorOrModeratorOrAdmin)
from api.serializers import (
    CategorySerializer, CommentSerializer,
    GenreSerializer, ReviewSerializer,
    SelfEditUserSerializer, SignUpSerializer,
    TitleReadSerializer, TitleWriteSerializer,
    TokenSerializer, UserSerializer,
)
from reviews.admin import User
from reviews.models import Category, Genre, Review, Title


@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    """Регистрация нового пользователя и/или отправка проверочного кода."""
    serializer = SignUpSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    username = serializer.validated_data['username']
    email = serializer.validated_data['email']
    try:
        user, _ = User.objects.get_or_create(username=username, email=email)
    except IntegrityError as error:
        raise ValidationError(
            {'username': 'username уже занят.'}
            if 'reviews_user.username' in error.args
            else {'email': 'email уже занят.'}
        )
    user.confirmation_code = ''.join(
        random.choices(settings.CONFIRMATION_CODE_CHARS,
                       k=settings.CONFIRMATION_CODE_LENGTH)
    )
    user.save(update_fields=['confirmation_code'])
    send_mail(
        subject='Код подтверждения YaMDb',
        message=f'Ваш код подтверждения: {user.confirmation_code}',
        recipient_list=[user.email],
        from_email=settings.DEFAULT_FROM_EMAIL,
        fail_silently=False,
    )
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def token(request):
    """
    Выдача JWT-токена при предъявлении валидного одноразового кода.
    Код после успешной выдачи токена «сбрасывается»
    (становится недействительным).
    """
    serializer = TokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    username = serializer.validated_data['username']
    code = serializer.validated_data['confirmation_code']

    user = get_object_or_404(User, username=username)

    if user.confirmation_code != code or not code:
        user.confirmation_code = ''
        user.save(update_fields=['confirmation_code'])
        raise ValidationError(
            {'confirmation_code': 'Неверный код подтверждения.'}
        )
    token_str = str(AccessToken.for_user(user))
    return Response({'token': token_str}, status=status.HTTP_200_OK)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = (drf_filters.SearchFilter,)
    search_fields = ('username',)
    lookup_field = 'username'
    permission_classes = (IsAdminOnlyPermission,)
    http_method_names = ('get', 'post', 'patch', 'delete')

    @action(detail=False, methods=['get', 'patch'],
            permission_classes=[IsAuthenticated],
            url_path=settings.PROFILE_RESERVED_SEGMENT)
    def user_self_page(self, request):
        """Работа со своей учётной записью."""
        user = request.user
        if request.method != 'PATCH':
            return Response(
                self.get_serializer(user).data,
                status=status.HTTP_200_OK
            )
        serializer = SelfEditUserSerializer(
            user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class ListCreateDestroySlugViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    """
    Только список, создание и удаление.
    Для моделей с полем slug.
    """
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (drf_filters.SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'
    http_method_names = ('get', 'post', 'delete')


class CategoryViewSet(ListCreateDestroySlugViewSet):
    """Вьюмет для работы с категориями."""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class GenreViewSet(ListCreateDestroySlugViewSet):
    """Вьюмет для работы с жанрами."""

    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class TitleFilter(filters.FilterSet):
    """Фильтр для жанров."""

    genre = filters.ModelMultipleChoiceFilter(
        field_name='genre__slug',
        to_field_name='slug',
        queryset=Genre.objects.all(),
        conjoined=False,
    )
    category = filters.CharFilter(field_name='category__slug')
    year = filters.NumberFilter(field_name='year')
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = Title
        fields = ['genre', 'category', 'year', 'name']


class TitleViewSet(viewsets.ModelViewSet):
    """Вьюмет для работы с произведениями."""

    queryset = Title.objects.annotate(
        rating=Avg('reviews__score')
    ).order_by(*Title._meta.ordering)
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TitleFilter
    http_method_names = ('get', 'post', 'patch', 'delete')

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return TitleReadSerializer
        return TitleWriteSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    """Вьюмет для работы с отзывами."""

    serializer_class = ReviewSerializer
    http_method_names = ('get', 'post', 'patch', 'delete')
    permission_classes = (IsAuthorOrModeratorOrAdmin,)

    def get_title(self):
        return get_object_or_404(Title, id=self.kwargs['title_id'])

    def get_queryset(self):
        return self.get_title().reviews.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, title=self.get_title())


class CommentViewSet(viewsets.ModelViewSet):
    """Вьюмет для работы с коментариями."""

    serializer_class = CommentSerializer
    http_method_names = ('get', 'post', 'patch', 'delete')
    permission_classes = (IsAuthorOrModeratorOrAdmin,)

    def get_review(self):
        return get_object_or_404(Review, id=self.kwargs['review_id'])

    def get_queryset(self):
        return self.get_review().comments.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, review=self.get_review())
