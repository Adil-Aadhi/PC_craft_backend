from django.urls import path
from .views import ProfileView,UpdateProfileImage,DeleteProfileImage,UserAddressView

urlpatterns = [
    path("profile/", ProfileView.as_view(), name="profile"),
    path("profile/update-image/", UpdateProfileImage.as_view(), name="update_image"),
    path("profile/delete-image/", DeleteProfileImage.as_view(), name="delete_image"),
    path("profile/user-address/", UserAddressView.as_view(), name="user_address"),
    path("profile/user-address/<int:id>/", UserAddressView.as_view(), name="update_user_address"),
    path("profile/user-address/<int:id>/set-default/", UserAddressView.as_view(), name="default_user_address"),
]