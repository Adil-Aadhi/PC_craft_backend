from django.urls import path
from .views import RegisterAPIView,LoginAPIView,TokenRefreshCookieView,GoogleAuthAPIView,LogoutAPIView


urlpatterns = [
    path('register/<str:role>/', RegisterAPIView.as_view(), name='register'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('logout/', LogoutAPIView.as_view(), name='logout'),
    path('refresh/', TokenRefreshCookieView.as_view(), name='token'),
    path('google/', GoogleAuthAPIView.as_view(), name='google'),
]