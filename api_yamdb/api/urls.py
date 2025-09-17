from django.urls import include, path

from api.views import TokenView

auth_urls = [
    # path('signup/', signup, name='signup'),
    path('token/', TokenView.as_view(), name='token'),
]

urlpatterns = [
    path('v1/auth/', include(auth_urls))
]
