from django.urls import include, path

from .views import ReviewListCreateView, ReviewDetailView
from api.views import SignUpView, TokenView

auth_urls = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('token/', TokenView.as_view(), name='token'),
]

urlpatterns = [
    path('v1/auth/', include(auth_urls)),
    path('api/v1/titles/<int:title_id>/reviews/', ReviewListCreateView.as_view(), name='reviews-list-create'),
    path('api/v1/titles/<int:title_id>/reviews/<int:review_id>/', ReviewDetailView.as_view(), name='review-detail'),
path('v1/', include('api.v1.urls')),

]
