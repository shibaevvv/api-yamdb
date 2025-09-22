from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import SignUpView, TokenView, UserViewSet

v1_router = DefaultRouter()
v1_router.register('users', UserViewSet, basename='users')

auth_urls = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('token/', TokenView.as_view(), name='token'),
]

urlpatterns = [
    path('v1/auth/', include(auth_urls)),
    path('v1/', include(v1_router.urls)),
]
