from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializer import RegisterSerializer,LoginSerializer,ForgotPasswordSerializer,VerifyOTPSerializer,ResetPasswordSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework import status
from django.contrib.auth import get_user_model
import requests
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .utils import generate_otp
from .models import PasswordResetOTP
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta


# Create your views here.

User = get_user_model()


class RegisterAPIView(APIView):

    @swagger_auto_schema(
        operation_summary="User registration",
        operation_description="Register a new user account",
        request_body=RegisterSerializer,
        responses={
            201: openapi.Response(
                description="User registered successfully",
                schema=RegisterSerializer  # optional but BEST
            ),
            400: openapi.Response(
                description="Validation error"
            ),
        },
        tags=["Authentication"],
    )

    def post(self, request, role):
        serializer = RegisterSerializer(
            data=request.data,
            context={'role': role})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        user_data = {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "role": user.role,
        }

        response = Response(
            {
                "access": str(access),
                "user": user_data,
            },
            status=status.HTTP_201_CREATED
        )

        response.set_cookie(
            key="refresh_token",
            value=str(refresh),
            httponly=True,
            secure=False,        # True in production
            samesite="Lax",
            max_age=24 * 60 * 60,
        )
        return response
    
class LoginAPIView(APIView):

    @swagger_auto_schema(
    operation_summary="User login",
    operation_description="Authenticate user and return JWT tokens",
    request_body=LoginSerializer,
    responses={
        200: LoginSerializer,
        400: openapi.Response(
            description="Invalid input data"
        ),
        401: openapi.Response(
            description="Invalid email or password"
        ),
    },
    tags=["Authentication"],)

    def post(self,request):
        serializer=LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        # user_data = serializer.validated_data["user_data"]
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        worker_profile = getattr(user, "worker_profile", None)

        user_data = {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "kyc_status": worker_profile.kyc_status if worker_profile else None
        }

        response = Response({
            "access": str(access),
            "user":user_data
        }, status=status.HTTP_200_OK)

        response.set_cookie(
            key='refresh_token',
            value=str(refresh),
            httponly=True,
            secure=False,       # True in production (HTTPS)
            samesite='Lax',
            max_age=24 * 60 * 60
        )

        return response
    
class TokenRefreshCookieView(APIView):
    authentication_classes = [] 
    permission_classes = [] 

    @swagger_auto_schema(
        operation_summary="Refresh access token",
        operation_description=(
            "Refresh JWT access token using refresh token stored in HTTP-only cookie"
        ),
        request_body=None,  # 👈 IMPORTANT
        responses={
            200: openapi.Response(
                description="Access token refreshed successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "access": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="New access token"
                        )
                    }
                )
            ),
            401: openapi.Response(
                description="Invalid or expired refresh token"
            ),
        },
        tags=["Authentication"],
    )


    def post(self, request):
        refresh_token_str = request.COOKIES.get('refresh_token')

        if not refresh_token_str:
            return Response(
                {"detail": "Refresh token not found"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            # ✅ convert STRING → RefreshToken object
            old_refresh = RefreshToken(refresh_token_str)

            # 🔐 blacklist old refresh (rotation)
            old_refresh.blacklist()

            # ✅ extract user_id from TOKEN PAYLOAD
            user_id = old_refresh['user_id']
            user = User.objects.get(id=user_id)

            # 🔄 issue NEW refresh + access
            new_refresh = RefreshToken.for_user(user)

            response = Response(
                {"access": str(new_refresh.access_token)},
                status=status.HTTP_200_OK
            )

            response.set_cookie(
                key='refresh_token',
                value=str(new_refresh),
                httponly=True,
                secure=False,   # True in production
                samesite='Lax',
                max_age=24 * 60 * 60
            )

            return response

        except (TokenError, User.DoesNotExist):
            return Response(
                {"detail": "Invalid or expired refresh token"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        

class GoogleAuthAPIView(APIView):

    @swagger_auto_schema(
        operation_summary="Google authentication",
        operation_description=(
            "Authenticate or register user using Google OAuth access token. "
            "Refresh token is stored in an HTTP-only cookie."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["access_token"],
            properties={
                "access_token": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Google OAuth access token"
                ),
                "role": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=["user", "worker"],
                    description="User role (optional)",
                    default="user"
                ),
            }
        ),
        responses={
            200: openapi.Response(
                description="Login successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "access": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="JWT access token"
                        ),
                        "user": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                "email": openapi.Schema(type=openapi.TYPE_STRING),
                                "username": openapi.Schema(type=openapi.TYPE_STRING),
                                "role": openapi.Schema(type=openapi.TYPE_STRING),
                            }
                        ),
                    }
                )
            ),
            201: openapi.Response(
                description="User registered via Google"
            ),
            400: openapi.Response(
                description="Invalid Google token or provider mismatch"
            ),
        },
        tags=["Authentication"],
    )

    def post(self, request):

        access_token = request.data.get("access_token")
        role = request.data.get("role", "user")

        # 🔹 Get user info from Google using access token
        google_response = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={
                "Authorization": f"Bearer {access_token}"
            }
        )

        if google_response.status_code != 200:
            return Response(
                {"error": "Invalid Google token"},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = google_response.json()
        email = data["email"]
        name = data.get("name", "")

        user = User.objects.filter(email=email).first()

        if user:
            if user.auth_provider != "google":
                return Response(
                    {"error": "Use email/password login"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            user = User.objects.create(
                email=email,
                username=email.split("@")[0],
                role=role,
                auth_provider="google"
            )

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        user_data = {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "role": user.role
        }

        response = Response(
            {
                "access": str(access),
                "user": user_data
            },
            status=status.HTTP_200_OK
        )

        response.set_cookie(
            key="refresh_token",
            value=str(refresh),
            httponly=True,
            secure=False,  # True in production
            samesite="Lax",
            max_age=24 * 60 * 60
        )

        return response

class LogoutAPIView(APIView):

    @ swagger_auto_schema(
            operation_summary="User Logout",
            operation_description=("Logs out the user by blacklisting the refresh token "
            "stored in HTTP-only cookie and removing the cookie."),
            request_body=None,
            responses={
                205:openapi.Response(
                    description="Logged out succesfully"
                ),
                401:openapi.Response(
                    description="No valid refresh token found"
                ),
            },
            tags={"Authentication"}
    )
    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")

        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception:
                pass  # already invalid / expired

        response = Response(
            {"message": "Logged out successfully"},
            status=status.HTTP_205_RESET_CONTENT
        )

        response.delete_cookie("refresh_token", path="/")
        return response

class ForgotPasswordView(APIView):

    @swagger_auto_schema(
        operation_summary="Forgot password - send OTP",
        operation_description=(
            "Send a 6-digit OTP to the user's registered email. "
            "OTP is valid for 5 minutes."
        ),
        request_body=ForgotPasswordSerializer,
        responses={
            200: openapi.Response(
                description="OTP sent successfully",
                examples={
                    "application/json": {
                        "message": "OTP sent to email"
                    }
                },
            ),
            404: openapi.Response(
                description="User not found",
                examples={
                    "application/json": {
                        "error": "User with this email does not exist"
                    }
                },
            ),
            400: openapi.Response(
                description="Invalid input data"
            ),
        },
        tags=["Authentication"],
    )


    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"error": "User with this email does not exist"},
                status=status.HTTP_404_NOT_FOUND,
            )

        otp = generate_otp()

        PasswordResetOTP.objects.create(user=user, otp=otp)

        send_mail(
            subject="Your Password Reset OTP",
            message=f"Your OTP is {otp}. It is valid for 5 minutes.",
            from_email="your_email@gmail.com",
            recipient_list=[email],
        )

        return Response({"message": "OTP sent to email"}, status=200)
    
class VerifyOTPView(APIView):

    @swagger_auto_schema(
        operation_summary="Verify OTP",
        operation_description=(
            "Verify the OTP sent to the user's email for password reset. "
            "OTP must be valid and not expired."
        ),
        request_body=VerifyOTPSerializer,
        responses={
            200: openapi.Response(
                description="OTP verified successfully",
                examples={
                    "application/json": {
                        "message": "OTP verified"
                    }
                },
            ),
            400: openapi.Response(
                description="Invalid email / OTP / expired OTP",
                examples={
                    "application/json": {
                        "error": "Invalid OTP"
                    }
                },
            ),
        },
        tags=["Authentication"],
    )

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]

        try:
            user = User.objects.get(email=email)
            otp_obj = PasswordResetOTP.objects.filter(
                user=user, otp=otp, is_verified=False
            ).last()
        except User.DoesNotExist:
            return Response({"error": "Invalid email"}, status=400)

        if not otp_obj:
            return Response({"error": "Invalid OTP"}, status=400)

        if otp_obj.is_expired():
            return Response({"error": "OTP expired"}, status=400)

        otp_obj.is_verified = True
        otp_obj.save()

        return Response({"message": "OTP verified"}, status=200)
    
class ResetPasswordView(APIView):

    @swagger_auto_schema(
        operation_summary="Reset password",
        operation_description=(
            "Reset the user's password after OTP verification. "
            "Requires email and a strong new password."
        ),
        request_body=ResetPasswordSerializer,
        responses={
            200: openapi.Response(
                description="Password reset successful",
                examples={
                    "application/json": {
                        "message": "Password reset successful"
                    }
                },
            ),
            400: openapi.Response(
                description="Validation error / OTP not verified / OTP expired",
                examples={
                    "application/json": {
                        "password": [
                            "Minimum 8 characters required",
                            "At least one uppercase letter required"
                        ]
                    }
                },
            ),
        },
        tags=["Authentication"],
    )

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        # 🔐 Check user exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"email": ["User with this email does not exist"]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 🔐 Get latest verified OTP
        otp_obj = PasswordResetOTP.objects.filter(
            user=user,
            is_verified=True,
        ).last()

        if not otp_obj:
            return Response(
                {"otp": ["OTP not verified"]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 🔐 Check OTP expiry (example: 5 minutes)
        if otp_obj.created_at < timezone.now() - timedelta(minutes=5):
            otp_obj.delete()
            return Response(
                {"otp": ["OTP expired. Please request a new one"]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 🔐 Set new password (hashed)
        user.set_password(password)
        user.save()

        # 🔐 Delete OTP after success
        otp_obj.delete()

        return Response(
            {"message": "Password reset successful"},
            status=status.HTTP_200_OK,
        )
