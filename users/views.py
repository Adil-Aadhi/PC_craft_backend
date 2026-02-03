from django.shortcuts import render
from Authentication.models import UserProfile
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .serializers import ProfileSerializer,ProfileUpdateSerializer,ProfileImageSerializer,UserAddressSerializer
from rest_framework.response import Response
import cloudinary.uploader
from rest_framework import status
from .models import Address
from Authentication.models import User
import random
from django.core.mail import send_mail
from django.conf import settings
from .models import EmailOTP

# Create your views here.

class ProfileView(APIView):
    permission_classes=[IsAuthenticated]

    def get(self,request):
        profile = request.user.user_profile
        serializer = ProfileSerializer(profile)
        return Response(serializer.data,status=status.HTTP_200_OK)
    
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
    
class ChangePasswordView(APIView):
    permission_classes=[IsAuthenticated]

    def post(self,request):
        user=request.user
        old_password=request.data.get('old_password')
        new_password=request.data.get('new_password')
        confirm_password = request.data.get("confirm_password")

        if not old_password or not new_password or not confirm_password:
            return Response(
                {"detail": "All fields are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not user.check_password(old_password):
            return Response(
                {"detail": "Old password is incorrect."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if new_password != confirm_password:
            return Response(
                {"detail": "New passwords do not match."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if old_password == new_password:
            return Response(
                {"detail": "New password must be different from old password."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(new_password)
        user.save()

        return Response(
            {"detail": "Password changed successfully. Please log in again."},
            status=status.HTTP_200_OK
        )
            

class ChangeEmailView(APIView):
    def post(self,request):
        email=request.data.get('email')
        if not email:
            return Response(
                {"error": "Email is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        if email != request.user.email:
            return Response(
                {"error": "Email does not match your account"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        
        otp = random.randint(100000, 999999)

        EmailOTP.objects.create(
            user=request.user,
            email=email,
            otp=otp
        )
        

        send_mail(
            subject="Confirm Email Change",
            message=f"Your OTP for EMAIL change is: {otp}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        return Response(
            {"message": "OTP sent to email"},
            status=status.HTTP_200_OK
        )
    
class EmailChangeVerifyView(APIView):
    def post(self,request):
        otp=request.data.get('otp')
        if not otp:
            return Response({"error":"enter otp"},status=status.HTTP_400_BAD_REQUEST)
        
        record = EmailOTP.objects.filter(
            user=request.user,
            otp=otp,
            is_verified=False
        ).first()

        if not record:
            return Response({"error": "Invalid OTP"}, status=400)
        
        if record.is_expired():
            return Response({"error": "OTP expired"}, status=400)
        
        record.is_verified = True
        record.save()

        request.session["email_verified"] = True

        return Response(
            {"message": "Email verified. You can now change email."},
            status=status.HTTP_200_OK
        )
    
class UpdateEmailView(APIView):
    def post(self,request):
        if not request.session.get("email_verified"):
            return Response(
                {"error": "Verify email first"},
                status=status.HTTP_403_FORBIDDEN
            )
        new_email = request.data.get("email")

        if User.objects.filter(email=new_email).exists():
            return Response(
                {"error": "Email already in use"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        request.user.email = new_email
        request.user.save()

        request.session.pop("email_verified", None)

        return Response(
            {"message": "Email changed successfully"},
            status=status.HTTP_200_OK
        )
        
        
            


