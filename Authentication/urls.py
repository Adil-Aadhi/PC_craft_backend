from django.urls import path
from .views import RegisterAPIView,LoginAPIView,TokenRefreshCookieView,GoogleAuthAPIView,LogoutAPIView,ForgotPasswordView,VerifyOTPView,ResetPasswordView


urlpatterns = [
    path('register/<str:role>/', RegisterAPIView.as_view(), name='register'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('logout/', LogoutAPIView.as_view(), name='logout'),
    path('refresh/', TokenRefreshCookieView.as_view(), name='token'),
    path('google/', GoogleAuthAPIView.as_view(), name='google'),
    path('forgetpassword/', ForgotPasswordView.as_view(), name='forgetpassword'),
    path('verifyotp/', VerifyOTPView.as_view(), name='verifyotp'),
    path('resetpassword/', ResetPasswordView.as_view(), name='resetpassword'),
]