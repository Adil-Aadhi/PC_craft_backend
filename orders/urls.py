from django.urls import path
from .views import MyOrdersView,CreateRazorpayOrderView,VerifyRazorpayPaymentView,CancelOrderView,WorkerOrdersView,WorkerOrderDetailView,VerifyComponentAPIView,WorkerProgressAPIView,UpdateOrderStatusAPIView,CreateWorkerReviewAPIView

urlpatterns = [
    path("my-orders/", MyOrdersView.as_view(), name="my-orders"),
    path("create-razorpay-order/", CreateRazorpayOrderView.as_view(), name="create-razorpay"),
    path("verify-razorpay-payment/", VerifyRazorpayPaymentView.as_view(), name="verify-razorpay"),
    path("my-orders/cancel/<uuid:order_id>/", CancelOrderView.as_view(), name="cancel-order"),
    path("worker-project/", WorkerOrdersView.as_view(), name="worker-project"),
    path("worker-project/<uuid:order_id>/", WorkerOrderDetailView.as_view(), name="worker-project-individual"),
    path("worker-project/<uuid:order_id>/component/verify/", VerifyComponentAPIView.as_view(), name="worker-project-component-verify"),
    path("worker-project/<uuid:order_id>/component/progress/", WorkerProgressAPIView.as_view(), name="worker-project-component-progress"),
    path("<uuid:order_id>/update-status/", UpdateOrderStatusAPIView.as_view(), name="worker-project-status-update"),
    path("rating/create/", CreateWorkerReviewAPIView.as_view(), name="rating-create"),
]