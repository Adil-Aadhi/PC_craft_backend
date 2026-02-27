import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch, MagicMock
from Authentication.models import PasswordResetOTP
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


@pytest.mark.django_db
class TestRegisterAPIView:

    def setup_method(self):
        self.client = APIClient()

    def test_register_user_success(self):
        url = reverse("register", kwargs={"role": "user"})

        data = {
            "full_name": "Test User",
            "email": "testuser@example.com",
            "username": "testuser",
            "password": "StrongPass123!",
            "confirm_password": "StrongPass123!"
        }

        response = self.client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert "access" in response.data
        assert "user" in response.data

        # Check user created in DB
        assert User.objects.filter(email="testuser@example.com").exists()

        # Check refresh token cookie set
        assert "refresh_token" in response.cookies

    def test_register_worker_success(self):
        url = reverse("register", kwargs={"role": "worker"})

        data = {
            "full_name": "Worker One",
            "email": "worker@example.com",
            "username": "worker1",
            "password": "StrongPass123!",
            "confirm_password": "StrongPass123!"
        }

        response = self.client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        user = User.objects.get(email="worker@example.com")
        assert user.role == "worker"

    def test_password_mismatch(self):
        url = reverse("register", kwargs={"role": "user"})

        data = {
            "full_name": "Mismatch",
            "email": "mismatch@example.com",
            "username": "mismatchuser",
            "password": "StrongPass123!",
            "confirm_password": "WrongPass123!"
        }

        response = self.client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_role(self):
        url = reverse("register", kwargs={"role": "admin"})

        data = {
            "full_name": "Invalid Role",
            "email": "invalid@example.com",
            "username": "invaliduser",
            "password": "StrongPass123!",
            "confirm_password": "StrongPass123!"
        }

        response = self.client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_duplicate_email(self):
        User.objects.create_user(
            username="existing",
            email="duplicate@example.com",
            password="StrongPass123!",
            role="user"
        )

        url = reverse("register", kwargs={"role": "user"})

        data = {
            "full_name": "Duplicate",
            "email": "duplicate@example.com",
            "username": "newusername",
            "password": "StrongPass123!",
            "confirm_password": "StrongPass123!"
        }

        response = self.client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_duplicate_username(self):
        User.objects.create_user(
            username="duplicateuser",
            email="unique@example.com",
            password="StrongPass123!",
            role="user"
        )

        url = reverse("register", kwargs={"role": "user"})

        data = {
            "full_name": "Duplicate Username",
            "email": "newemail@example.com",
            "username": "duplicateuser",
            "password": "StrongPass123!",
            "confirm_password": "StrongPass123!"
        }

        response = self.client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
class TestLoginAPIView:

    def setup_method(self):
        self.client = APIClient()
        self.url = reverse("login")   # make sure your login url name is "login"

    def test_login_success(self):
        user = User.objects.create_user(
            username="loginuser",
            email="login@example.com",
            password="StrongPass123!",
            role="user"
        )

        data = {
            "username": "loginuser",
            "password": "StrongPass123!"
        }

        response = self.client.post(self.url, data)

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "user" in response.data
        assert response.data["user"]["email"] == "login@example.com"

        # Check refresh cookie
        assert "refresh_token" in response.cookies

    def test_login_wrong_password(self):
        User.objects.create_user(
            username="wrongpass",
            email="wrong@example.com",
            password="CorrectPass123",
            role="user"
        )

        data = {
            "username": "wrongpass",
            "password": "WrongPass"
        }

        response = self.client.post(self.url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_nonexistent_user(self):
        data = {
            "username": "nouser",
            "password": "NoPass123"
        }

        response = self.client.post(self.url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_disabled_user(self):
        user = User.objects.create_user(
            username="disableduser",
            email="disabled@example.com",
            password="StrongPass123!",
            role="user"
        )

        user.is_active = False
        user.save()

        data = {
            "username": "disableduser",
            "password": "StrongPass123!"
        }

        response = self.client.post(self.url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
class TestTokenRefreshCookieView:

    def setup_method(self):
        self.client = APIClient()
        self.url = reverse("token")  # make sure your url name matches

    def test_refresh_success(self):
        user = User.objects.create_user(
            username="refreshuser",
            email="refresh@example.com",
            password="StrongPass123!",
            role="user"
        )

        refresh = RefreshToken.for_user(user)

        # Set cookie manually
        self.client.cookies["refresh_token"] = str(refresh)

        response = self.client.post(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh_token" in response.cookies

    def test_refresh_no_cookie(self):
        response = self.client.post(self.url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_invalid_token(self):
        self.client.cookies["refresh_token"] = "invalidtoken123"

        response = self.client.post(self.url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
class TestGoogleAuthAPIView:

    def setup_method(self):
        self.client = APIClient()
        self.url = reverse("google")  # make sure URL name matches

    @patch("Authentication.views.requests.get")
    def test_google_register_new_user(self, mock_get):
        # Mock Google response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "email": "googleuser@example.com",
            "name": "Google User"
        }
        mock_get.return_value = mock_response

        data = {
            "access_token": "valid_google_token",
            "role": "user"
        }

        response = self.client.post(self.url, data)

        assert response.status_code == 200
        assert User.objects.filter(email="googleuser@example.com").exists()
        assert "access" in response.data
        assert "refresh_token" in response.cookies

    @patch("Authentication.views.requests.get")
    def test_google_login_existing_user(self, mock_get):
        user = User.objects.create(
            email="existinggoogle@example.com",
            username="existinggoogle",
            role="user",
            auth_provider="google"
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "email": "existinggoogle@example.com",
            "name": "Existing User"
        }
        mock_get.return_value = mock_response

        data = {"access_token": "valid_token"}

        response = self.client.post(self.url, data)

        assert response.status_code == 200
        assert response.data["user"]["email"] == "existinggoogle@example.com"

    @patch("Authentication.views.requests.get")
    def test_google_invalid_token(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        data = {"access_token": "invalid_token"}

        response = self.client.post(self.url, data)

        assert response.status_code == 400

    @patch("Authentication.views.requests.get")
    def test_google_provider_mismatch(self, mock_get):
        User.objects.create(
            email="normal@example.com",
            username="normaluser",
            role="user",
            auth_provider="email"
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "email": "normal@example.com",
            "name": "Normal User"
        }
        mock_get.return_value = mock_response

        data = {"access_token": "valid_token"}

        response = self.client.post(self.url, data)

        assert response.status_code == 400

@pytest.mark.django_db
class TestLogoutAPIView:

    def setup_method(self):
        self.client = APIClient()
        self.url = reverse("logout")  # make sure URL name matches

    def test_logout_with_valid_refresh(self):
        user = User.objects.create_user(
            username="logoutuser",
            email="logout@example.com",
            password="StrongPass123!",
            role="user"
        )

        refresh = RefreshToken.for_user(user)

        self.client.cookies["refresh_token"] = str(refresh)

        response = self.client.post(self.url)

        assert response.status_code == 205
        assert "refresh_token" in response.cookies
        assert response.cookies["refresh_token"].value == ""

    def test_logout_with_invalid_token(self):
        self.client.cookies["refresh_token"] = "invalidtoken123"

        response = self.client.post(self.url)

        assert response.status_code == 205

    def test_logout_without_cookie(self):
        response = self.client.post(self.url)

        assert response.status_code == 205


@pytest.mark.django_db
class TestForgotPasswordAPIView:

    def setup_method(self):
        self.client = APIClient()
        self.url = reverse("forgetpassword")

        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="StrongPass123!",
            role="user"
        )

    # ✅ SUCCESS CASE
    @patch("Authentication.views.send_mail")  # update path if different
    def test_forgot_password_valid_email(self, mock_send_mail):
        payload = {
            "email": "test@example.com"
        }

        response = self.client.post(self.url, payload, format="json")

        assert response.status_code == 200
        assert response.data["message"] == "OTP sent to email"

        # OTP created in DB
        assert PasswordResetOTP.objects.filter(user=self.user).exists()

        # Email function called
        mock_send_mail.assert_called_once()

    # ❌ USER NOT FOUND
    def test_forgot_password_user_not_found(self):
        payload = {
            "email": "nouser@example.com"
        }

        response = self.client.post(self.url, payload, format="json")

        assert response.status_code == 404
        assert response.data["error"] == "User with this email does not exist"

    # ❌ INVALID PAYLOAD (missing email)
    def test_forgot_password_invalid_payload(self):
        payload = {}

        response = self.client.post(self.url, payload, format="json")

        assert response.status_code == 400
        assert "email" in response.data

    # ✅ MULTIPLE OTP REQUESTS SHOULD CREATE NEW OTP
    @patch("Authentication.views.send_mail")
    def test_forgot_password_multiple_requests(self, mock_send_mail):
        payload = {
            "email": "test@example.com"
        }

        self.client.post(self.url, payload, format="json")
        self.client.post(self.url, payload, format="json")

        otp_count = PasswordResetOTP.objects.filter(user=self.user).count()

        assert otp_count == 2
        assert mock_send_mail.call_count == 2

@pytest.mark.django_db
class TestVerifyOTPAPIView:

    def setup_method(self):
        self.client = APIClient()
        self.url = reverse("verifyotp")

        self.user = User.objects.create_user(
            username="otpuser",
            email="otp@example.com",
            password="StrongPass123!",
            role="user"
        )

        self.otp = "123456"

        self.otp_obj = PasswordResetOTP.objects.create(
            user=self.user,
            otp=self.otp,
            is_verified=False
        )

    
    def test_verify_otp_success(self):
        payload = {
            "email": "otp@example.com",
            "otp": "123456"
        }

        response = self.client.post(self.url, payload, format="json")

        assert response.status_code == 200
        assert response.data["message"] == "OTP verified"

        self.otp_obj.refresh_from_db()
        assert self.otp_obj.is_verified is True

    
    def test_verify_otp_invalid_email(self):
        payload = {
            "email": "wrong@example.com",
            "otp": "123456"
        }

        response = self.client.post(self.url, payload, format="json")

        assert response.status_code == 400
        assert response.data["error"] == "Invalid email"

    
    def test_verify_otp_invalid_otp(self):
        payload = {
            "email": "otp@example.com",
            "otp": "000000"
        }

        response = self.client.post(self.url, payload, format="json")

        assert response.status_code == 400
        assert response.data["error"] == "Invalid OTP"

    #  EXPIRED OTP
    def test_verify_otp_expired(self):
        # simulate expiry (older than 5 minutes)
        self.otp_obj.created_at = timezone.now() - timedelta(minutes=10)
        self.otp_obj.save()

        payload = {
            "email": "otp@example.com",
            "otp": "123456"
        }

        response = self.client.post(self.url, payload, format="json")

        assert response.status_code == 400
        assert response.data["error"] == "OTP expired"

    #  ALREADY VERIFIED OTP SHOULD FAIL
    def test_verify_otp_already_verified(self):
        self.otp_obj.is_verified = True
        self.otp_obj.save()

        payload = {
            "email": "otp@example.com",
            "otp": "123456"
        }

        response = self.client.post(self.url, payload, format="json")

        assert response.status_code == 400
        assert response.data["error"] == "Invalid OTP"

@pytest.mark.django_db
class TestResetPasswordAPIView:

    def setup_method(self):
        self.client = APIClient()
        self.url = reverse("resetpassword") 

        self.user = User.objects.create_user(
            username="resetuser",
            email="reset@example.com",
            password="OldPass123",
            role="user"
        )

        self.otp_obj = PasswordResetOTP.objects.create(
            user=self.user,
            otp="123456",
            is_verified=True
        )

    #  SUCCESS CASE
    def test_reset_password_success(self):
        payload = {
            "email": "reset@example.com",
            "password": "NewStrongPass123!"
        }

        response = self.client.post(self.url, payload, format="json")

        assert response.status_code == 200
        assert response.data["message"] == "Password reset successful"

        # password updated
        self.user.refresh_from_db()
        assert self.user.check_password("NewStrongPass123!") is True

        # OTP deleted after success
        assert PasswordResetOTP.objects.filter(id=self.otp_obj.id).exists() is False

    #  USER NOT FOUND
    def test_reset_password_user_not_found(self):
        payload = {
            "email": "nouser@example.com",
            "password": "NewStrongPass123!"
        }

        response = self.client.post(self.url, payload, format="json")

        assert response.status_code == 400
        assert "email" in response.data

    #  OTP NOT VERIFIED
    def test_reset_password_otp_not_verified(self):
        self.otp_obj.is_verified = False
        self.otp_obj.save()

        payload = {
            "email": "reset@example.com",
            "password": "NewStrongPass123!"
        }

        response = self.client.post(self.url, payload, format="json")

        assert response.status_code == 400
        assert "otp" in response.data
        assert response.data["otp"][0] == "OTP not verified"

    #  OTP EXPIRED
    def test_reset_password_otp_expired(self):
        self.otp_obj.created_at = timezone.now() - timedelta(minutes=10)
        self.otp_obj.save()

        payload = {
            "email": "reset@example.com",
            "password": "NewStrongPass123!"
        }

        response = self.client.post(self.url, payload, format="json")

        assert response.status_code == 400
        assert "otp" in response.data
        assert "OTP expired" in response.data["otp"][0]

        # OTP should be deleted after expiry
        assert PasswordResetOTP.objects.filter(id=self.otp_obj.id).exists() is False

    #  INVALID PAYLOAD (WEAK PASSWORD OR MISSING FIELD)
    def test_reset_password_invalid_payload(self):
        payload = {
            "email": "reset@example.com",
        }

        response = self.client.post(self.url, payload, format="json")

        assert response.status_code == 400
        assert "password" in response.data    