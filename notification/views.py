from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import FCMToken,Notification


# Create your views here.
class SaveFCMTokenAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            token = request.data.get("fcm_token") or request.data.get("token")

            if not token:
                return Response({"error": "Token required"}, status=400)

            FCMToken.objects.update_or_create(
                user=request.user,
                defaults={"token": token}
            )

            return Response({"message": "FCM token saved"}, status=200)

        except Exception as e:
            print("FCM SAVE ERROR:", str(e))
            return Response({"error": "Server error"}, status=500)
    
class WorkerNotificationListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(
            user=request.user
        ).order_by("-created_at")

        data = [
            {
                "id": n.id,
                "title": n.title,
                "message": n.message,
                "is_read": n.is_read,
                "created_at": n.created_at,
                "chat_request_id": n.chat_request.id if n.chat_request else None,
                "chat_request_status": (
                    n.chat_request.status if n.chat_request else None
                ),
            }
            for n in notifications
        ]

        return Response(data)