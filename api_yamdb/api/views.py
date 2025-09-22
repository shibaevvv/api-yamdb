from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from reviews.models import Title, Review
from .serializers import ReviewSerializer
from .permissions import IsAuthorOrModeratorOrAdmin


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
