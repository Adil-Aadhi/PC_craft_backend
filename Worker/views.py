from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import ProfileImageSerializer,WorkerPersonalInfoSerializer,WorkerBannerImageSerializer,WorkerKycProgressSerializer
from .models import WorkerKycProgress
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi



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

        
