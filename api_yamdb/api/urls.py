from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet,
    GenreViewSet,
    TitleViewSet,
    SignUpView,
    TokenView,
    ReviewListCreateView,
    ReviewDetailView,
)
from api.views import SignUpView, TokenView

router = DefaultRouter()
router.register('categories', CategoryViewSet, basename='category')
router.register('genres', GenreViewSet, basename='genre')
router.register('titles', TitleViewSet, basename='title')

urlpatterns = [
    path('v1/auth/signup/', SignUpView.as_view(), name='signup'),
    path('v1/auth/token/', TokenView.as_view(), name='token'),
    path('v1/', include(router.urls)),
    path('v1/titles/<int:title_id>/reviews/', ReviewListCreateView.as_view(), name='reviews-list-create'),
    path('v1/titles/<int:title_id>/reviews/<int:review_id>/', ReviewDetailView.as_view(), name='review-detail'),
]
