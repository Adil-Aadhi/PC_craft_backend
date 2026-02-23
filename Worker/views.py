from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import ProfileImageSerializer,WorkerPersonalInfoSerializer,WorkerBannerImageSerializer,WorkerKycProgressSerializer,ChatRequestCreateSerializer,WorkerListSerializer,ChatRequestActionSerializer,WorkerDetailsSerializer,WorkerIdentityKYCSerializer,WorkerPayoutSerializer
from .models import WorkerKycProgress,ChatRequest,ChatRoom,ChatMessage,WorkerIdentityKYC,WorkerPayoutDetails
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from Authentication.models import WorkerProfile
from django.db import connection
from django.db.models import Exists, OuterRef
import uuid
from django.utils import timezone
from django.db import transaction
from notification.models import FCMToken,Notification
from notification.utils import send_fcm_notification





# Create your views here.
class WorkerProfileImage(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get worker profile image",
        operation_description=(
            "Retrieve the authenticated worker's profile image"
        ),
        responses={
            200: ProfileImageSerializer,
            401: openapi.Response(description="Unauthorized"),
            404: openapi.Response(description="Worker profile not found"),
        },
        tags=["Worker Profile"],
    )

    def get(self,request):
        worker=getattr(request.user, "worker_profile", None)
        if not worker:
            return Response(
                {"error": "Worker profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = ProfileImageSerializer(worker)
        return Response(serializer.data, status=status.HTTP_200_OK)


    @swagger_auto_schema(
        operation_summary="Update worker profile image",
        operation_description=(
            "Upload or update the authenticated worker's profile image"
        ),
        request_body=ProfileImageSerializer,
        responses={
            200: ProfileImageSerializer,
            400: openapi.Response(description="Invalid image data"),
            401: openapi.Response(description="Unauthorized"),
            404: openapi.Response(description="Worker profile not found"),
        },
        tags=["Worker Profile"],
    )

    def patch(self, request):
        worker = getattr(request.user, "worker_profile", None)

        if not worker:
            return Response(
                {"error": "Worker profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProfileImageSerializer(
            worker,
            data=request.data,
            partial=True
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()  

        return Response(
            serializer.data,  
            status=status.HTTP_200_OK
        )
    

class WorkerPersonalInfoView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get worker personal information",
        operation_description=(
            "Retrieve personal information of the authenticated worker"
        ),
        responses={
            200: WorkerPersonalInfoSerializer,
            401: openapi.Response(description="Unauthorized"),
            404: openapi.Response(description="Worker profile not found"),
        },
        tags=["Worker Profile"],
    )

    def get(self, request):
        worker = getattr(request.user, "worker_profile", None)
        if not worker:
            return Response(
                {"detail": "Worker profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        user_profile = request.user.user_profile
        serializer = WorkerPersonalInfoSerializer(user_profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Update worker personal information",
        operation_description=(
            "Partially update the authenticated worker's personal information"
        ),
        request_body=WorkerPersonalInfoSerializer,
        responses={
            200: WorkerPersonalInfoSerializer,
            400: openapi.Response(description="Invalid input data"),
            401: openapi.Response(description="Unauthorized"),
            404: openapi.Response(description="Worker profile not found"),
        },
        tags=["Worker Profile"],
    )

    def patch(self, request):
        worker = getattr(request.user, "worker_profile", None)
        if not worker:
            return Response(
                {"detail": "Worker profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        user_profile = request.user.user_profile

        serializer = WorkerPersonalInfoSerializer(
            user_profile,
            data=request.data,
            partial=True
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

class WorkerBannerImageView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get worker banner image",
        operation_description=(
            "Retrieve the authenticated worker's banner image"
        ),
        responses={
            200: WorkerBannerImageSerializer,
            401: openapi.Response(description="Unauthorized"),
            404: openapi.Response(description="Worker profile not found"),
        },
        tags=["Worker Profile"],
    )

    def get(self, request):
        worker = getattr(request.user, "worker_profile", None)
        if not worker:
            return Response(
                {"detail": "Worker profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = WorkerBannerImageSerializer(worker)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_summary="Update worker banner image",
        operation_description=(
            "Upload or update the authenticated worker's banner image"
        ),
        request_body=WorkerBannerImageSerializer,
        responses={
            200: WorkerBannerImageSerializer,
            400: openapi.Response(description="Invalid image data"),
            401: openapi.Response(description="Unauthorized"),
            404: openapi.Response(description="Worker profile not found"),
        },
        tags=["Worker Profile"],
    )

    def patch(self, request):
        worker = getattr(request.user, "worker_profile", None)
        if not worker:
            return Response(
                {"detail": "Worker profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = WorkerBannerImageSerializer(
            worker,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)
    

class WorkerKycProgressView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get worker KYC progress",
        operation_description=(
            "Retrieve the current KYC progress status "
            "of the authenticated worker"
        ),
        responses={
            200: WorkerKycProgressSerializer,
            401: openapi.Response(description="Unauthorized"),
        },
        tags=["Worker KYC"],
    )

    def get(self, request):
        obj, _ = WorkerKycProgress.objects.get_or_create(worker=request.user)
        serializer = WorkerKycProgressSerializer(obj)
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_summary="Update worker KYC progress",
        operation_description=(
            "Partially update the worker's KYC progress status"
        ),
        request_body=WorkerKycProgressSerializer,
        responses={
            200: WorkerKycProgressSerializer,
            400: openapi.Response(description="Invalid input data"),
            401: openapi.Response(description="Unauthorized"),
        },
        tags=["Worker KYC"],
    )

    def post(self, request):
        obj, _ = WorkerKycProgress.objects.get_or_create(worker=request.user)
        serializer = WorkerKycProgressSerializer(
            obj, data=request.data, partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class WorkerListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get worker list",
        operation_description=(
            "Returns all workers with their profile details and a boolean "
            "`has_requested` indicating whether the authenticated user has "
            "already sent a chat request."
        ),
        responses={
            200: openapi.Response(
                description="Worker list fetched successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "user_id": openapi.Schema(
                                type=openapi.TYPE_INTEGER,
                                example=12
                            ),
                            "name": openapi.Schema(
                                type=openapi.TYPE_STRING,
                                example="john"
                            ),
                            "rating": openapi.Schema(
                                type=openapi.TYPE_NUMBER,
                                format="float",
                                example=4.5
                            ),
                            "skills": openapi.Schema(
                                type=openapi.TYPE_STRING,
                                example="Electrician"
                            ),
                            "profile_image": openapi.Schema(
                                type=openapi.TYPE_STRING,
                                format="uri",
                                example="https://res.cloudinary.com/demo/profile.jpg"
                            ),
                            "hourly_rate": openapi.Schema(
                                type=openapi.TYPE_STRING,
                                example="500.00"
                            ),
                            "has_requested": openapi.Schema(
                                type=openapi.TYPE_BOOLEAN,
                                example=True
                            ),
                        },
                    ),
                ),
            ),
            401: "Unauthorized",
        },
        security=[{"Bearer": []}],
    )

    def get(self, request):
        pending_requests = ChatRequest.objects.filter(
            sender=request.user,
            receiver=OuterRef("user"),
            status="pending"
        )

        accepted_requests = ChatRequest.objects.filter(
            sender=request.user,
            receiver=OuterRef("user"),
            status="accepted"
        )

        workers = (
            WorkerProfile.objects
            .select_related("user")
            .annotate(has_requested=Exists(pending_requests),
                      is_connected=Exists(accepted_requests)
            )
            .filter(is_connected=False) # 👈 hide accepted users
        )

        serializer = WorkerListSerializer(workers, many=True)
        return Response(serializer.data)


class ChatRequestCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Send chat request to worker",
        operation_description=(
            "Allows an authenticated user to send a chat request to a worker "
            "by providing the worker's `receiver_id`. "
            "Prevents sending requests to yourself, non-workers, or duplicate pending requests."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["receiver_id"],
            properties={
                "receiver_id": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    example=15,
                    description="User ID of the worker you want to chat with"
                ),
            },
        ),
        responses={
            201: openapi.Response(
                description="Chat request sent successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Chat request sent"
                        ),
                        "request_id": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            example=101
                        ),
                        "status": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="pending"
                        ),
                    },
                ),
            ),
            400: openapi.Response(
                description="Validation error",
                examples={
                    "application/json": {
                        "receiver_id": [
                            "You cannot send request to yourself"
                        ]
                    }
                },
            ),
            401: "Unauthorized",
        },
        security=[{"Bearer": []}],
    )

    def post(self, request):
        serializer = ChatRequestCreateSerializer(
            data=request.data,
            context={"request": request}
        )


        if serializer.is_valid():
            chat_request = serializer.save()

            receiver = chat_request.receiver
            Notification.objects.create(
                user=chat_request.receiver,
                title="New Chat Request 💬",
                message=f"{request.user.username} sent you a chat request",
                chat_request=chat_request
            )
            tokens = FCMToken.objects.filter(user=receiver)
            for t in tokens:
                try:
                    send_fcm_notification(
                        token=t.token,
                        title="New Chat Request 💬",
                        body=f"{request.user.username} sent you a chat request",
                        data={
                            "type": "chat_request",
                            "request_id": str(chat_request.id),
                            "sender_id": str(request.user.id),
                        }
                    )
                except Exception as e:
                    print("FCM error:", e)

            return Response(
                {
                    "message": "Chat request sent",
                    "request_id": chat_request.id,
                    "status": chat_request.status,
                },
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class ChatRequestActionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Accept or reject chat request",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["status"],
            properties={
                "status": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=["accepted", "rejected"],
                    example="accepted"
                )
            },
        ),
        responses={
            200: openapi.Response(
                description="Request handled",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "status": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="accepted"
                        ),
                        "room_created": openapi.Schema(
                            type=openapi.TYPE_BOOLEAN,
                            example=True
                        ),
                    },
                ),
            ),
            400: "Already handled / invalid status",
            403: "Not allowed",
            404: "Request not found",
        },
        security=[{"Bearer": []}],
    )

    def patch(self, request, request_id):
        try:
            chat_request = ChatRequest.objects.get(id=request_id)
        except ChatRequest.DoesNotExist:
            return Response({"detail": "Request not found"}, status=404)

        # only receiver (worker) can accept/reject
        if chat_request.receiver != request.user:
            return Response({"detail": "Not allowed"}, status=403)

        serializer = ChatRequestActionSerializer(
            chat_request,
            data=request.data,
            partial=True
        )

        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data["status"]

        # prevent double action
        if chat_request.status != "pending":
            return Response({"detail": "Already handled"}, status=400)

        with transaction.atomic():
            chat_request.status = new_status
            chat_request.save()

            # 🔥 IF ACCEPTED → CREATE ROOM + AUTO MESSAGE
            if new_status == "accepted":

                ids = sorted([chat_request.sender.id, chat_request.receiver.id])
                room_name = f"room_{ids[0]}_{ids[1]}"

                room = ChatRoom.objects.create(
                    room_name=room_name,
                    request=chat_request
                )

                room.participants.add(
                    chat_request.sender,
                    chat_request.receiver
                )

                # 🔥 auto first message
                ChatMessage.objects.create(
                    id=uuid.uuid4(),
                    room_name=room.room_name,
                    sender=chat_request.receiver,
                    message="Hi 👋 How can I help you?",
                    is_delivered=True,
                    is_seen=False,
                    timestamp=timezone.now()
                )

        return Response({
            "status": chat_request.status,
            "room_created": new_status == "accepted"
        }, status=status.HTTP_200_OK)
    

class WorkerDetailsView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get worker profile details",
        operation_description="Returns the authenticated worker's profile details.",
        responses={
            200: openapi.Response(
                description="Worker details fetched successfully",
                schema=WorkerDetailsSerializer()
            ),
            403: openapi.Response(
                description="Only workers can access this endpoint",
                examples={
                    "application/json": {
                        "detail": "Only workers have profiles."
                    }
                }
            ),
            404: openapi.Response(
                description="Worker profile not found",
                examples={
                    "application/json": {
                        "detail": "Worker profile not found."
                    }
                }
            ),
        }
    )

    def get(self, request):
        if request.user.role != "worker":
            return Response(
                {"detail": "Only workers have profiles."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            worker = WorkerProfile.objects.get(user=request.user)
        except WorkerProfile.DoesNotExist:
            return Response(
                {"detail": "Worker profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = WorkerDetailsSerializer(worker)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Update worker details",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "description": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    example="Experienced electrician for home wiring"
                ),
                "skills": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    example="Electrical, Wiring, Installation"
                ),
                "experience_years": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    example=5
                ),
                "hourly_rate": openapi.Schema(
                    type=openapi.TYPE_NUMBER,
                    example=500
                ),
            },
        ),
        responses={
            200: openapi.Response(
                description="Worker details updated successfully",
                examples={
                    "application/json": {
                        "detail": "Worker details updated successfully"
                    }
                },
            ),
            400: "Validation error",
            404: "Worker profile not found",
            401: "Unauthorized",
        },
        security=[{"Bearer": []}],
    )

    def patch(self, request):
        try:
            worker_profile = request.user.worker_profile
        except WorkerProfile.DoesNotExist:
            return Response(
                {"detail": "Worker profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = WorkerDetailsSerializer(
            worker_profile,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WorkerIdentityKYCAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get identity KYC",
        responses={
            200: openapi.Response(
                description="Identity KYC fetched",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "id_type": openapi.Schema(type=openapi.TYPE_STRING, example="aadhaar"),
                        "masked_id_number": openapi.Schema(type=openapi.TYPE_STRING, example="XXXXXX1234"),
                        "id_front_url": openapi.Schema(type=openapi.TYPE_STRING, format="uri"),
                        "id_front_id": openapi.Schema(type=openapi.TYPE_STRING),
                        "id_back_url": openapi.Schema(type=openapi.TYPE_STRING, format="uri"),
                        "id_back_id": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            404: "Identity KYC not found",
            401: "Unauthorized",
        },
        security=[{"Bearer": []}],
        tags=["Worker KYC"],
    )

    def get(self, request):
        try:
            kyc = WorkerIdentityKYC.objects.get(user=request.user)
            serializer = WorkerIdentityKYCSerializer(kyc)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except WorkerIdentityKYC.DoesNotExist:
            return Response(
                {"detail": "Identity KYC not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
    @swagger_auto_schema(
        operation_summary="Create or update identity KYC",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["id_type", "id_number", "id_front_url", "id_front_id"],
            properties={
                "id_type": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=["aadhaar", "pan", "dl", "voter"],
                    example="aadhaar"
                ),
                "id_number": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    example="123412341234"
                ),
                "id_front_url": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format="uri",
                    example="https://res.cloudinary.com/demo/front.jpg"
                ),
                "id_front_id": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    example="kyc/front_abc"
                ),
                "id_back_url": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format="uri",
                    example="https://res.cloudinary.com/demo/back.jpg"
                ),
                "id_back_id": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    example="kyc/back_xyz"
                ),
            },
        ),
        responses={
            200: openapi.Response(
                description="Identity KYC saved",
                examples={
                    "application/json": {
                        "message": "Identity KYC saved successfully"
                    }
                },
            ),
            400: "Validation error",
            401: "Unauthorized",
        },
        security=[{"Bearer": []}],
        tags=["Worker KYC"],
    )

    def post(self, request):
        serializer = WorkerIdentityKYCSerializer(
            data=request.data,
            context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()  # uses update_or_create internally
            return Response(
                {"message": "Identity KYC saved successfully"},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class WorkerPayoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get worker UPI payout details",
        responses={
            200: openapi.Response(
                description="UPI fetched",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "upi_id": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="name@upi"
                        )
                    },
                ),
            ),
            404: openapi.Response(
                description="UPI not found",
                examples={
                    "application/json": {
                        "upi_id": None
                    }
                },
            ),
            401: "Unauthorized",
        },
        security=[{"Bearer": []}],
        tags=["Worker KYC"],
    )

    def get(self, request):
        try:
            payout = WorkerPayoutDetails.objects.get(user=request.user)
            serializer = WorkerPayoutSerializer(payout)
            return Response(serializer.data)
        except WorkerPayoutDetails.DoesNotExist:
            return Response({"upi_id": None},status=status.HTTP_404_NOT_FOUND)
        

    @swagger_auto_schema(
        operation_summary="Create or update UPI payout details",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["upi_id"],
            properties={
                "upi_id": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    example="name@upi"
                )
            },
        ),
        responses={
            200: openapi.Response(
                description="UPI saved successfully",
                examples={
                    "application/json": {
                        "message": "UPI saved successfully"
                    }
                },
            ),
            400: "Invalid UPI ID",
            401: "Unauthorized",
        },
        security=[{"Bearer": []}],
        tags=["Worker KYC"],
    )

    def post(self, request):
        serializer = WorkerPayoutSerializer(
            data=request.data,
            context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "UPI saved successfully"},status=status.HTTP_200_OK)
        return Response(serializer.errors, status=400)
    
class WorkerKycStatusChangeAPIView(APIView):
    permission_classes =[IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Submit KYC",
        operation_description="Marks the worker KYC status as pending.",
        responses={
            200: openapi.Response(
                description="KYC submitted successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "kyc_status": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="pending"
                        ),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="KYC submitted"
                        ),
                    },
                ),
            ),
            404: openapi.Response(
                description="Worker profile not found",
                examples={
                    "application/json": {
                        "error": "invalid user"
                    }
                },
            ),
            401: "Unauthorized",
        },
        security=[{"Bearer": []}],
        tags=["Worker KYC"],
    )

    def post(self,request):
        try:
            kyc=WorkerProfile.objects.get(user=request.user)
            kyc.kyc_status="pending"
            kyc.save()
            return Response(
                {"kyc_status": kyc.kyc_status, "message": "KYC submitted"},
                status=status.HTTP_200_OK
            )
        except WorkerProfile.DoesNotExist:
            return Response({"error":"invalid user"},status=status.HTTP_404_NOT_FOUND)
        