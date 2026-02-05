from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import ProfileImageSerializer,WorkerPersonalInfoSerializer,WorkerBannerImageSerializer


# Create your views here.
class WorkerProfileImage(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request):
        worker=getattr(request.user, "worker_profile", None)
        print("GET PROFILE IMAGE HIT")
        if not worker:
            return Response(
                {"error": "Worker profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = ProfileImageSerializer(worker)
        return Response(serializer.data, status=status.HTTP_200_OK)



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

    def get(self, request):
        worker = getattr(request.user, "worker_profile", None)
        if not worker:
            return Response(
                {"detail": "Worker profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = WorkerBannerImageSerializer(worker)
        return Response(serializer.data, status=status.HTTP_200_OK)

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
        
