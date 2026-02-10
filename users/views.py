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
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Create your views here.

class ProfileView(APIView):
    permission_classes=[IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get user profile",
        operation_description="Retrieve the authenticated user's profile details",
        responses={
            200: ProfileSerializer,
            401: openapi.Response(description="Unauthorized"),
        },
        tags=["Profile"],
    )

    def get(self,request):
        profile = request.user.user_profile
        serializer = ProfileSerializer(profile)
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_summary="Update user profile",
        operation_description=(
            "Partially update the authenticated user's profile details"
        ),
        request_body=ProfileUpdateSerializer,
        responses={
            200: ProfileSerializer,
            400: openapi.Response(description="Invalid input data"),
            401: openapi.Response(description="Unauthorized"),
        },
        tags=["Profile"],
    )
    
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

    @swagger_auto_schema(
        operation_summary="Update profile image",
        operation_description=(
            "Upload or update the authenticated user's profile image"
        ),
        request_body=ProfileImageSerializer,
        responses={
            200: openapi.Response(
                description="Profile image updated successfully"
            ),
            400: openapi.Response(
                description="Invalid image data"
            ),
            401: openapi.Response(
                description="Unauthorized"
            ),
        },
        tags=["Profile"],
    )

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
    
    @swagger_auto_schema(
        operation_summary="Delete profile image",
        operation_description=(
            "Delete the authenticated user's profile image"
        ),
        request_body=None,
        responses={
            200: openapi.Response(
                description="Profile image deleted successfully"
            ),
            401: openapi.Response(
                description="Unauthorized"
            ),
            404: openapi.Response(
                description="No profile image found"
            ),
        },
        tags=["Profile"],
    )

    def delete(self,request):
        profile = request.user.user_profile
        if profile.profile_image_id:
            cloudinary.uploader.destroy(profile.profile_image_id)

            profile.profile_image = None
            profile.profile_image_id = None
            profile.save()

            return Response({"message": "Profile image deleted"},status=status.HTTP_301_MOVED_PERMANENTLY)
    

class UserAddressView(APIView):
    permission_classes=[IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="List user addresses",
        operation_description="Retrieve all addresses of the authenticated user",
        responses={
            200: UserAddressSerializer(many=True),
            401: openapi.Response(description="Unauthorized"),
        },
        tags=["Address"],
    )

    def get(self,request):
        addresses = Address.objects.filter(user=request.user)
        serializer = UserAddressSerializer(addresses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_summary="Create new address",
        operation_description=(
            "Create a new address for the authenticated user. "
            "If marked as default, previous default address will be unset."
        ),
        request_body=UserAddressSerializer,
        responses={
            201: UserAddressSerializer,
            400: openapi.Response(description="Invalid input data"),
            401: openapi.Response(description="Unauthorized"),
        },
        tags=["Address"],
    )
    
    def post(self, request):
        serializer = UserAddressSerializer(data=request.data)

        if serializer.is_valid():

            #  If new address is marked as default, unset previous defaults
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

    
class UserAddressDetailView(APIView):
    permission_classes=[IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Update address",
        operation_description="Update a specific address of the authenticated user",
        manual_parameters=[
            openapi.Parameter(
                "id",
                openapi.IN_PATH,
                description="Address ID",
                type=openapi.TYPE_INTEGER,
                required=True,
            )
        ],
        request_body=UserAddressSerializer,
        responses={
            200: UserAddressSerializer,
            400: openapi.Response(description="Invalid input data"),
            401: openapi.Response(description="Unauthorized"),
            404: openapi.Response(description="Address not found"),
        },
        tags=["Address"],
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
    

    @swagger_auto_schema(
        operation_summary="Delete address",
        operation_description=(
            "Delete a specific address of the authenticated user. "
            "If the deleted address was default, another address "
            "will be automatically set as default."
        ),
        manual_parameters=[
            openapi.Parameter(
                "id",
                openapi.IN_PATH,
                description="Address ID",
                type=openapi.TYPE_INTEGER,
                required=True,
            )
        ],
        request_body=None,
        responses={
            204: openapi.Response(description="Address deleted successfully"),
            401: openapi.Response(description="Unauthorized"),
            404: openapi.Response(description="Address not found"),
        },
        tags=["Address"],
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

        #  If default was deleted, set another as default
        if was_default:
            next_address = Address.objects.filter(
                user=request.user
            ).first()

            if next_address:
                next_address.is_default = True
                next_address.save()

        return Response(status=status.HTTP_204_NO_CONTENT)
    
class SetDefaultAddressView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Set default address",
        operation_description=(
            "Set the specified address as the default address "
            "for the authenticated user"
        ),
        manual_parameters=[
            openapi.Parameter(
                "id",
                openapi.IN_PATH,
                description="Address ID",
                type=openapi.TYPE_INTEGER,
                required=True,
            )
        ],
        request_body=None, 
        responses={
            200: openapi.Response(
                description="Default address updated successfully"
            ),
            401: openapi.Response(
                description="Unauthorized"
            ),
            404: openapi.Response(
                description="Address not found"
            ),
        },
        tags=["Address"],
    )

    def patch(self, request, id):
        try:
            address = Address.objects.get(id=id, user=request.user)
        except Address.DoesNotExist:
            return Response(
                {"detail": "Address not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        
        Address.objects.filter(
            user=request.user,
            is_default=True
        ).update(is_default=False)

        #  Set new default
        address.is_default = True
        address.save()

        return Response(
            {"detail": "Default address updated"},
            status=status.HTTP_200_OK
        )

    
class ChangePasswordView(APIView):
    permission_classes=[IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Change password",
        operation_description=(
            "Change the authenticated user's password by providing "
            "the old password and a new password."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["old_password", "new_password", "confirm_password"],
            properties={
                "old_password": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Current password"
                ),
                "new_password": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="New password"
                ),
                "confirm_password": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Confirm new password"
                ),
            },
        ),
        responses={
            200: openapi.Response(
                description="Password changed successfully"
            ),
            400: openapi.Response(
                description="Validation error"
            ),
            401: openapi.Response(
                description="Unauthorized"
            ),
        },
        tags=["Password"],
    )

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

    @swagger_auto_schema(
        operation_summary="Request email change OTP",
        operation_description=(
            "Send an OTP to the user's current email address "
            "to confirm email change."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["email"],
            properties={
                "email": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format="email",
                    description="Current registered email address"
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="OTP sent to email successfully"
            ),
            400: openapi.Response(
                description="Invalid email or email mismatch"
            ),
            401: openapi.Response(
                description="Unauthorized"
            ),
        },
        tags=["Email"],
    )
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

    @swagger_auto_schema(
        operation_summary="Verify email change OTP",
        operation_description=(
            "Verify the OTP sent to the user's email address "
            "before allowing email change."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["otp"],
            properties={
                "otp": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="OTP sent to user's email"
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="Email verified successfully"
            ),
            400: openapi.Response(
                description="Invalid or expired OTP"
            ),
            401: openapi.Response(
                description="Unauthorized"
            ),
        },
        tags=["Email"],
    )

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

    @swagger_auto_schema(
        operation_summary="Update email address",
        operation_description=(
            "Update the authenticated user's email address. "
            "Requires prior email OTP verification."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["email"],
            properties={
                "email": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format="email",
                    description="New email address"
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="Email changed successfully"
            ),
            400: openapi.Response(
                description="Email already in use"
            ),
            403: openapi.Response(
                description="Email not verified"
            ),
            401: openapi.Response(
                description="Unauthorized"
            ),
        },
        tags=["Email"],
    )
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