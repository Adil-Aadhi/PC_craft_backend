import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch, MagicMock

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
            "password": "StrongPass123",
            "confirm_password": "StrongPass123"
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
            "password": "StrongPass123",
            "confirm_password": "StrongPass123"
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
            "password": "StrongPass123",
            "confirm_password": "WrongPass123"
        }

        response = self.client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_role(self):
        url = reverse("register", kwargs={"role": "admin"})

        data = {
            "full_name": "Invalid Role",
            "email": "invalid@example.com",
            "username": "invaliduser",
            "password": "StrongPass123",
            "confirm_password": "StrongPass123"
        }

        response = self.client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_duplicate_email(self):
        User.objects.create_user(
            username="existing",
            email="duplicate@example.com",
            password="StrongPass123",
            role="user"
        )

        url = reverse("register", kwargs={"role": "user"})

        data = {
            "full_name": "Duplicate",
            "email": "duplicate@example.com",
            "username": "newusername",
            "password": "StrongPass123",
            "confirm_password": "StrongPass123"
        }

        response = self.client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_duplicate_username(self):
        User.objects.create_user(
            username="duplicateuser",
            email="unique@example.com",
            password="StrongPass123",
            role="user"
        )

        url = reverse("register", kwargs={"role": "user"})

        data = {
            "full_name": "Duplicate Username",
            "email": "newemail@example.com",
            "username": "duplicateuser",
            "password": "StrongPass123",
            "confirm_password": "StrongPass123"
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
            password="StrongPass123",
            role="user"
        )

        data = {
            "username": "loginuser",
            "password": "StrongPass123"
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
            password="StrongPass123",
            role="user"
        )

        user.is_active = False
        user.save()

        data = {
            "username": "disableduser",
            "password": "StrongPass123"
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
            password="StrongPass123",
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
            password="StrongPass123",
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