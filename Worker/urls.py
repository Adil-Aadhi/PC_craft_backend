from django.urls import path
from .views import WorkerProfileImage,WorkerPersonalInfoView,WorkerBannerImageView,WorkerKycProgressView,ChatRequestCreateAPIView,WorkerListAPIView,ChatRequestActionAPIView,WorkerDetailsView,WorkerIdentityKYCAPIView,WorkerPayoutAPIView,WorkerKycStatusChangeAPIView,WorkerRevenueAPIView,WorkerDashboardView

urlpatterns=[
    path("profile-image/", WorkerProfileImage.as_view(),name="update_worker_profile"),
    path("profile/personal-info/", WorkerPersonalInfoView.as_view(),name="worker-personal-info"),
    path("profile/worker-details/",WorkerDetailsView.as_view(),name="worker-details-update"),
    path("profile/worker-kyc/identity/", WorkerIdentityKYCAPIView.as_view(),name="worker-verification-update"),
    path("profile/kyc/payout/", WorkerPayoutAPIView.as_view(),name="worker-Payout"),
    path("profile/banner-image/", WorkerBannerImageView.as_view(),name="worker-banner-image"),
    path("kyc/progress/", WorkerKycProgressView.as_view(),name="worker-kyc-progress"),
    path("chat/requests/", ChatRequestCreateAPIView.as_view(), name="chat-request-create"),
    path("worker_list/", WorkerListAPIView.as_view(), name="worker-list"),
    path("chat/request/<int:request_id>/action/",ChatRequestActionAPIView.as_view(),name="chat-request-action"), 
    path("kyc/submit/",WorkerKycStatusChangeAPIView.as_view(),name="chat-request-action"),
    path("revenue/", WorkerRevenueAPIView.as_view(),name="worker-revenue"),
    path("dashboard/", WorkerDashboardView.as_view(),name="worker-dashboard")
]