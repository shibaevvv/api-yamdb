from rest_framework import permissions, status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken

from api.serializers import TokenSerializer
from users.models import User


class TokenView(APIView):
    """Возвращает JWT-токен зарегистрированного пользователя."""
    permission_classes = [permissions.AllowAny]

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
