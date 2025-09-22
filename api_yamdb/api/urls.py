from django.urls import path
from .views import ReviewListCreateView, ReviewDetailView

urlpatterns = [
    path('api/v1/titles/<int:title_id>/reviews/', ReviewListCreateView.as_view(), name='reviews-list-create'),
    path('api/v1/titles/<int:title_id>/reviews/<int:review_id>/', ReviewDetailView.as_view(), name='review-detail'),
]
