from django.shortcuts import render
from Authentication.models import UserProfile
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .serializers import ProfileSerializer,ProfileUpdateSerializer,ProfileImageSerializer,UserAddressSerializer
from rest_framework.response import Response
import cloudinary.uploader
from rest_framework import status
from .models import Address

# Create your views here.

class ProfileView(APIView):
    permission_classes=[IsAuthenticated]

    def get(self,request):
        profile = request.user.user_profile
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)
    
    def patch(self,request):

        profile = request.user.user_profile
        serializer=ProfileUpdateSerializer(profile,data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(ProfileSerializer(profile).data, status=status.HTTP_200_OK)
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
class UpdateProfileImage(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        profile = request.user.user_profile

        serializer = ProfileImageSerializer(
            profile,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Profile image updated"},
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
class DeleteProfileImage(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self,request):
        profile = request.user.user_profile
        if profile.profile_image_id:
            cloudinary.uploader.destroy(profile.profile_image_id)

            profile.profile_image = None
            profile.profile_image_id = None
            profile.save()

            return Response({"message": "Profile image deleted"})

class UserAddressView(APIView):
    permission_classes=[IsAuthenticated]

    def get(self,request):
        addresses = Address.objects.filter(user=request.user)
       
        if not addresses.exists():
            return Response(
                {"message": "No addresses found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = UserAddressSerializer(addresses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = UserAddressSerializer(data=request.data)

        if serializer.is_valid():

            # 🔒 If new address is marked as default, unset previous defaults
            if serializer.validated_data.get("is_default") is True:
                Address.objects.filter(
                    user=request.user,
                    is_default=True
                ).update(is_default=False)

            serializer.save(user=request.user)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        print(serializer.errors)
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


    def put(self, request, id):
        try:
            address = Address.objects.get(id=id, user=request.user)
        except Address.DoesNotExist:
            return Response(
                {"detail": "Address not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = UserAddressSerializer(address, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, id):
        try:
            address = Address.objects.get(id=id, user=request.user)
        except Address.DoesNotExist:
            return Response(
                {"detail": "Address not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # 🔥 Unset previous default
        Address.objects.filter(
            user=request.user,
            is_default=True
        ).update(is_default=False)

        # 🔥 Set new default
        address.is_default = True
        address.save()

        return Response(
            {"detail": "Default address updated"},
            status=status.HTTP_200_OK
        )
    
    def delete(self, request, id):
        try:
            address = Address.objects.get(id=id, user=request.user)
        except Address.DoesNotExist:
            return Response(
                {"detail": "Address not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        was_default = address.is_default
        address.delete()

        # 🔒 If default was deleted, set another as default
        if was_default:
            next_address = Address.objects.filter(
                user=request.user
            ).first()

            if next_address:
                next_address.is_default = True
                next_address.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


