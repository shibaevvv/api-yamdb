import random

from django.core.mail import send_mail
from django.db import IntegrityError
from django.db.models import Avg
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters
from rest_framework import (
    filters as drf_filters, permissions, status, viewsets
)
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.views import APIView

from api.permissions import (IsAdminOnlyPermission, IsAdminOrReadOnly,
                             IsAuthorOrModeratorOrAdmin)
from api.serializers import (CategorySerializer, CommentSerializer,
                             GenreSerializer, ReviewSerializer,
                             SelfEditUserSerializer, SignUpSerializer,
                             TitleReadSerializer, TitleWriteSerializer,
                             TokenSerializer, UserSerializer)
from reviews.models import Category, Comment, Genre, Review, Title, User


class SignUpView(APIView):
    """Регистрация нового пользователя и/или отправка проверочного кода."""
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = User.objects.get(
                username=serializer.validated_data['username'],
                email=serializer.validated_data['email']
            )
        except User.DoesNotExist:
            if User.objects.filter(
                    email=serializer.validated_data['email']
            ).exists():
                raise ValidationError({'email': 'email уже занят.'})
            if User.objects.filter(
                    username=serializer.validated_data['username']
            ).exists():
                raise ValidationError({'username': 'username уже занят.'})
            user = User.objects.create_user(**serializer.validated_data)
            user.save()
        user.confirmation_code = str(random.randint(100000, 999999))
        user.save(update_fields=['confirmation_code'])

        send_mail(
            subject='Проверочный код YaMDb',
            message=f'Ваш проверочный код: {user.confirmation_code}',
            recipient_list=(user.email,),
            from_email='noreply@yamdb.ru',
            fail_silently=True,
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class TokenView(APIView):
    """Возвращает JWT-токен зарегистрированного пользователя."""
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = TokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(
            User,
            username=serializer.validated_data['username']
        )
        if user.confirmation_code == (
            serializer.validated_data['confirmation_code']
        ):
            return Response(
                {'token': str(AccessToken.for_user(user))},
                status=status.HTTP_200_OK,
            )
        return Response(
            {'error': 'Отсутствует обязательное поле или оно некорректно!'},
            status=status.HTTP_400_BAD_REQUEST
        )


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с пользователями."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = (drf_filters.SearchFilter,)
    search_fields = ('username',)
    lookup_field = 'username'
    permission_classes = (IsAdminOnlyPermission,)
    http_method_names = ('get', 'post', 'patch', 'delete')

    @action(
        detail=False,
        methods=['get', 'patch'],
        permission_classes=(IsAuthenticated,),
        url_path='me'
    )
    def get_self_user_page(self, request):
        """Метод для работы с запросами к своей учетной записи."""
        user = request.user
        if request.method == 'PATCH':
            serializer = SelfEditUserSerializer(
                user,
                data=request.data,
                partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)


class StandardResultsSetPagination(PageNumberPagination):
    """Пагинация."""

    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class CategoryViewSet(viewsets.ModelViewSet):
    """Вьюмет для работы с категориями."""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (drf_filters.SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'

    def retrieve(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


class GenreViewSet(viewsets.ModelViewSet):
    """Вьюмет для работы с жанрами."""

    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (drf_filters.SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'

    def retrieve(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


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

    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TitleFilter

    def get_queryset(self):
        return Title.objects.annotate(_avg_score=Avg('reviews__score'))

    def get_serializer_class(self):
        return TitleReadSerializer if (
            self.action in ('list', 'retrieve')
        ) else TitleWriteSerializer

    def update(self, request, *args, **kwargs):
        if request.method != 'PATCH':
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return super().update(request, *args, **kwargs)


class ReviewViewSet(viewsets.ModelViewSet):
    """Вьюмет для работы с отзывами."""

    serializer_class = ReviewSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
    permission_classes = [IsAuthorOrModeratorOrAdmin]

    def get_title(self):
        return get_object_or_404(Title, pk=self.kwargs.get('title_id'))

    def get_queryset(self):
        return Review.objects.filter(
            title=self.get_title()
        ).order_by('-created_at')

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [AllowAny()]
        return super().get_permissions()

    def perform_create(self, serializer):
        title = self.get_title()
        try:
            serializer.save(author=self.request.user, title=title)
        except IntegrityError:
            raise ValidationError(
                'Вы уже оставляли отзыв на это произведение.'
            )

    def get_object(self):
        obj = super().get_object()
        self.check_object_permissions(self.request, obj)
        return obj


class CommentViewSet(viewsets.ModelViewSet):
    """Вьюмет для работы с коментариями."""

    serializer_class = CommentSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
    permission_classes = [IsAuthorOrModeratorOrAdmin]

    def get_review(self):
        title = get_object_or_404(Title, pk=self.kwargs.get('title_id'))
        return get_object_or_404(
            Review,
            pk=self.kwargs.get('review_id'),
            title=title
        )

    def get_queryset(self):
        return Comment.objects.filter(
            review=self.get_review()
        ).order_by('-created_at')

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [AllowAny()]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, review=self.get_review())

    def get_object(self):
        obj = super().get_object()
        self.check_object_permissions(self.request, obj)
        return obj
