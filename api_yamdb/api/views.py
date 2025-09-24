import random

from django.core.mail import send_mail
from django.db.models import Avg
from rest_framework import permissions, status, viewsets, filters as drf_filters
from rest_framework.exceptions import ValidationError, NotFound, PermissionDenied
from rest_framework.decorators import action

from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken

from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters


from reviews.models import Category, Genre, Title, Review
from .serializers import (
    CategorySerializer,
    GenreSerializer,
    TitleReadSerializer,
    TitleWriteSerializer,
    TokenSerializer,
    SignUpSerializer,
    ReviewSerializer,
)
from .permissions import IsAdminOrReadOnly, IsAuthorOrModeratorOrAdmin

from api.permissions import IsAdminOnlyPermission
from api.serializers import (
    TokenSerializer, SignUpSerializer, UserSerializer, SelfEditUserSerializer
)
from users.models import User


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
    filter_backends = (filters.SearchFilter,)
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
    page_size = 10  # можно настроить
    page_size_query_param = 'page_size'
    max_page_size = 100


class ReviewListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/titles/{title_id}/reviews/  -> список отзывов (AllowAny), с пагинацией
    POST /api/v1/titles/{title_id}/reviews/  -> создать отзыв (IsAuthenticated), 1 отзыв на пользователя+title
    """
    serializer_class = ReviewSerializer
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_title_or_404(self):
        title_id = self.kwargs.get('title_id')
        try:
            return Title.objects.get(pk=title_id)
        except Title.DoesNotExist:
            raise NotFound("Произведение не найдено")

    def get_queryset(self):
        title = self.get_title_or_404()
        return Review.objects.filter(title=title).order_by('-pub_date')

    def perform_create(self, serializer):
        title = self.get_title_or_404()
        # serializer.validate уже проверил уникальность отзыва на POST
        serializer.save(title=title, author=self.request.user)


class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/v1/titles/{title_id}/reviews/{review_id}/  -> получить отзыв (AllowAny)
    PATCH  /.../                                           -> частичное обновление (IsAuthorOrModeratorOrAdmin)
    DELETE /.../                                           -> удаление (IsAuthorOrModeratorOrAdmin)
    """
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthorOrModeratorOrAdmin]

    def get_object(self):
        title_id = self.kwargs.get('title_id')
        review_id = self.kwargs.get('review_id')

        # убедимся, что Title существует
        try:
            title = Title.objects.get(pk=title_id)
        except Title.DoesNotExist:
            raise NotFound("Произведение не найдено")

        # затем получим отзыв
        try:
            review = Review.objects.get(pk=review_id, title=title)
        except Review.DoesNotExist:
            raise NotFound("Отзыв не найден")

        # проверка прав на чтение реализуется в permission_classes:
        # allow read to any — но так как мы применяем кастомный пермишн,
        # стоит разрешить чтение всем: has_object_permission возвращает True для SAFE_METHODS.
        self.check_object_permissions(self.request, review)
        return review

class CategoryViewSet(viewsets.ModelViewSet):
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
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TitleFilter

    def get_queryset(self):
        return Title.objects.annotate(_avg_score=Avg('reviews__estimation'))

    def get_serializer_class(self):
        return TitleReadSerializer if self.action in ('list', 'retrieve') else TitleWriteSerializer

    def update(self, request, *args, **kwargs):
        if request.method != 'PATCH':
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return super().update(request, *args, **kwargs)

