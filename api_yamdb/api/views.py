import random

from django.core.mail import send_mail
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken

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
    """Получение JWT-токена зарегистрированного пользователя."""

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
            {'error': 'Отсутствует обязательное поле или оно некорректно'},
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
