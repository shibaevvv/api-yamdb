from django.urls import include, path
from rest_framework.routers import DefaultRouter


from api.views import (
  ReviewDetailView, ReviewListCreateView, SignUpView, TokenView, UserViewSet
)

v1_router = DefaultRouter()
v1_router.register('users', UserViewSet, basename='users')

auth_urls = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('token/', TokenView.as_view(), name='token'),
]

urlpatterns = [
    path('v1/auth/', include(auth_urls)),
    path('v1/', include(v1_router.urls)),
    path('api/v1/titles/<int:title_id>/reviews/', ReviewListCreateView.as_view(), name='reviews-list-create'),
    path('api/v1/titles/<int:title_id>/reviews/<int:review_id>/', ReviewDetailView.as_view(), name='review-detail'),
]
