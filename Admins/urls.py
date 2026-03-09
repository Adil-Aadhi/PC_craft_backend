from django.urls import path
from .views import AdminUsersView,ToggleUserStatus,AdminUserStatsView,PendingWorkersAPIView,UpdateWorkerKYCAPIView,CompletedOrdersAPIView,ApprovePaymentAPIView,AdminOrderListAPIView,AdminRevenueDashboardAPIView,AdminDashboardAPIView

urlpatterns = [
    path('users/', AdminUsersView.as_view(), name='admin-user'),
    path("users/<int:user_id>/toggle-status/", ToggleUserStatus.as_view(), name='admin-user-status'),
    path("users/stats/", AdminUserStatsView.as_view(), name="admin-user-stats"),
    path("workers/pending/", PendingWorkersAPIView.as_view(), name='admin-pending-worker'),
    path("workers/<int:pk>/kyc-update/", UpdateWorkerKYCAPIView.as_view(), name='admin-worker-update-kyc'),
    path("completion-requests/", CompletedOrdersAPIView.as_view(), name='completion-request'),
    path("approve-payment/<uuid:order_id>/",ApprovePaymentAPIView.as_view(),name="approve-payment"),
    path("all/orders/", AdminOrderListAPIView.as_view(),name="all-orders"),
    path("revenue/dashboard/", AdminRevenueDashboardAPIView.as_view(),name="admin-revenue-dashbaord"),
    path("dashboard/", AdminDashboardAPIView.as_view(),name="admin-dashboard")
]