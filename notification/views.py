from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import FCMToken,Notification
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


# Create your views here.
class SaveFCMTokenAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Save FCM token",
        operation_description=(
            "Save or update the authenticated user's Firebase Cloud Messaging (FCM) token "
            "for push notifications."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["fcm_token"],
            properties={
                "fcm_token": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Firebase Cloud Messaging device token"
                )
            },
            example={
                "fcm_token": "fcm_device_token_here"
            },
        ),
        responses={
            200: openapi.Response(
                description="FCM token saved successfully",
                examples={
                    "application/json": {
                        "message": "FCM token saved"
                    }
                },
            ),
            400: openapi.Response(
                description="Token missing",
                examples={
                    "application/json": {
                        "error": "Token required"
                    }
                },
            ),
            401: openapi.Response(description="Unauthorized"),
            500: openapi.Response(
                description="Server error",
                examples={
                    "application/json": {
                        "error": "Server error"
                    }
                },
            ),
        },
        tags=["Notifications"],
    )

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

    @swagger_auto_schema(
        operation_summary="Get user notifications",
        operation_description=(
            "Retrieve all notifications for the authenticated user "
            "(worker or customer), ordered by newest first."
        ),
        responses={
            200: openapi.Response(
                description="List of notifications",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                            "title": openapi.Schema(type=openapi.TYPE_STRING),
                            "message": openapi.Schema(type=openapi.TYPE_STRING),
                            "is_read": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                            "created_at": openapi.Schema(
                                type=openapi.TYPE_STRING,
                                format=openapi.FORMAT_DATETIME
                            ),
                            "chat_request_id": openapi.Schema(
                                type=openapi.TYPE_INTEGER,
                                nullable=True
                            ),
                            "chat_request_status": openapi.Schema(
                                type=openapi.TYPE_STRING,
                                nullable=True
                            ),
                        },
                    ),
                ),
                examples={
                    "application/json": [
                        {
                            "id": 1,
                            "title": "New Chat Request",
                            "message": "User requested build discussion",
                            "is_read": False,
                            "created_at": "2026-02-27T10:15:30Z",
                            "chat_request_id": 5,
                            "chat_request_status": "pending"
                        }
                    ]
                },
            ),
            401: openapi.Response(description="Unauthorized"),
        },
        tags=["Notifications"],
    )

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