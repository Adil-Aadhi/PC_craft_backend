from django.urls import path
from .views import ProfileView,UpdateProfileImage,UserAddressView,ChangePasswordView,ChangeEmailView,EmailChangeVerifyView,UpdateEmailView,UserAddressDetailView,SetDefaultAddressView,MeAPIView,ChatListAPIView

urlpatterns = [
    path("profile/", ProfileView.as_view(), name="profile"),
    path("auth/me/", MeAPIView.as_view(), name="auth-me"),
    path("profile/update-image/", UpdateProfileImage.as_view(), name="update_image"),
    path("profile/user-address/", UserAddressView.as_view(), name="user_address"),
    path("profile/user-address/<int:id>/", UserAddressDetailView.as_view(), name="update_user_address"),
    path("profile/user-address/<int:id>/set-default/", SetDefaultAddressView.as_view(), name="default_user_address"),
    path("profile/change_password/", ChangePasswordView.as_view(), name="change_password"),
    path("profile/change_email/", ChangeEmailView.as_view(), name="change_email"),
    path("profile/change_email/verify_email/", EmailChangeVerifyView.as_view(), name="verify_email"),
    path("profile/change_email/update_email/", UpdateEmailView.as_view(), name="update_email"),
    path("chat/list/", ChatListAPIView.as_view(), name="chat-list"),
]