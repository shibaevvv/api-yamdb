import random

from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Avg
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters
from rest_framework import (
    filters as drf_filters, status, viewsets, mixins
)
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import SAFE_METHODS, AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken

from api.permissions import (IsAdminOnlyPermission, IsAdminOrReadOnly,
                             IsAuthorOrModeratorOrAdmin)
from api.serializers import (CategorySerializer, CommentSerializer,
                             GenreSerializer, ReviewSerializer,
                             SelfEditUserSerializer, SignUpSerializer,
                             TitleReadSerializer, TitleWriteSerializer,
                             TokenSerializer, UserSerializer)
from reviews.admin import User
from reviews.models import Category, Comment, Genre, Review, Title


@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    """Регистрация нового пользователя и/или отправка проверочного кода."""
    serializer = SignUpSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    username = serializer.validated_data['username']
    email = serializer.validated_data['email']

    if User.objects.filter(email=email).exclude(username=username).exists():
        raise ValidationError({'email': 'Этот e-mail уже занят.'})
    if User.objects.filter(username=username).exclude(email=email).exists():
        raise ValidationError({'username': 'Этот username уже занят.'})

    user, created = User.objects.get_or_create(
        username=username,
        defaults={'email': email}
    )

    code = ''.join(
        random.choices(settings.CONFIRMATION_CODE_CHARS,
                       k=settings.CONFIRMATION_CODE_LENGTH)
    )
    user.confirmation_code = code
    user.save(update_fields=['confirmation_code'])

    send_mail(
        subject='Код подтверждения YaMDb',
        message=f'Ваш код подтверждения: {code}',
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
        raise ValidationError(
            {'confirmation_code': 'Неверный код подтверждения.'}
        )

    user.confirmation_code = ''
    user.save(update_fields=['confirmation_code'])

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

    ME_URL_PATH = 'me'

    @action(detail=False, methods=['get', 'patch'],
            permission_classes=[IsAuthenticated],
            url_path=ME_URL_PATH)
    def me(self, request):
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


class StandardResultsSetPagination(PageNumberPagination):
    """Пагинация."""

    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


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
        _avg_score=Avg('reviews__score')
    ).order_by('-year', 'name')
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

    def get_queryset(self):
        title_id = self.kwargs['title_id']
        return Review.objects.filter(title_id=title_id)

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [AllowAny()]
        return super().get_permissions()

    def perform_create(self, serializer):
        title = get_object_or_404(Title, pk=self.kwargs['title_id'])
        serializer.save(author=self.request.user, title=title)


class CommentViewSet(viewsets.ModelViewSet):
    """Вьюмет для работы с коментариями."""

    serializer_class = CommentSerializer
    http_method_names = ('get', 'post', 'patch', 'delete')
    permission_classes = (IsAuthorOrModeratorOrAdmin,)

    def get_queryset(self):
        review_id = self.kwargs['review_id']
        return Comment.objects.filter(review_id=review_id)

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [AllowAny()]
        return super().get_permissions()

    def perform_create(self, serializer):
        review = get_object_or_404(
            Review,
            pk=self.kwargs['review_id'],
            title_id=self.kwargs['title_id']
        )
        serializer.save(author=self.request.user, review=review)
