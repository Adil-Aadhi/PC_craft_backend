from django.urls import path
from .views import SaveFCMTokenAPIView,WorkerNotificationListAPIView

urlpatterns=[
    path("save-token/", SaveFCMTokenAPIView.as_view(),name="notification-savetoken"),
    path("worker/list-out/", WorkerNotificationListAPIView.as_view(),name="notificaton-worker-listout"),
]