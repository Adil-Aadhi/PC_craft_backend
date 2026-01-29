from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializer import RegisterSerializer,LoginSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework import status
from django.contrib.auth import get_user_model
import requests

# Create your views here.

User = get_user_model()

class RegisterAPIView(APIView):

    def post(self, request, role):
        serializer = RegisterSerializer(
            data=request.data,
            context={'role': role})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({"message": "Registered successfully"})
    
class LoginAPIView(APIView):

    def post(self,request):
        serializer=LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        user_data = serializer.validated_data["user_data"]
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

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
                    status=400
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
            status=205
        )

        response.delete_cookie("refresh_token", path="/")
        return response


    

        