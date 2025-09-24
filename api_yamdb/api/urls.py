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
    UserViewSet
)

v1_router = DefaultRouter()
v1_router.register('users', UserViewSet, basename='users')
router.register('categories', CategoryViewSet, basename='category')
router.register('genres', GenreViewSet, basename='genre')
router.register('titles', TitleViewSet, basename='title')

auth_urls = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('token/', TokenView.as_view(), name='token'),
]

urlpatterns = [
    path('v1/', include(v1_router.urls)),
    path('v1/auth/', include(auth_urls)),
    path('api/v1/titles/<int:title_id>/reviews/', ReviewListCreateView.as_view(), name='reviews-list-create'),
    path('api/v1/titles/<int:title_id>/reviews/<int:review_id>/', ReviewDetailView.as_view(), name='review-detail'),
]
