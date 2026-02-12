from django.urls import path
from .views import WorkerProfileImage,WorkerPersonalInfoView,WorkerBannerImageView,WorkerKycProgressView

urlpatterns=[
    path("profile-image/", WorkerProfileImage.as_view(),name="update_worker_profile"),
    path("profile/personal-info/", WorkerPersonalInfoView.as_view(),name="worker-personal-info"),
    path("profile/banner-image/", WorkerBannerImageView.as_view(),name="worker-banner-image"),
    path("kyc/progress/", WorkerKycProgressView.as_view(),name="worker-kyc-progress"),
]