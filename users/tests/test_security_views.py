import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from unittest.mock import patch
from users.models import EmailOTP

User = get_user_model()

@pytest.mark.django_db
class TestChangePasswordView:

    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="passuser",
            email="pass@example.com",
            password="OldPass123",
            role="user"
        )
        self.url = reverse("change_password")

    def test_change_password_success(self):
        self.client.force_authenticate(self.user)

        response = self.client.post(self.url, {
            "old_password": "OldPass123",
            "new_password": "NewPass123",
            "confirm_password": "NewPass123"
        })

        assert response.status_code == status.HTTP_200_OK
        self.user.refresh_from_db()
        assert self.user.check_password("NewPass123")

    def test_wrong_old_password(self):
        self.client.force_authenticate(self.user)

        response = self.client.post(self.url, {
            "old_password": "wrong",
            "new_password": "NewPass123",
            "confirm_password": "NewPass123"
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_new_password_same_as_old(self):
        self.client.force_authenticate(self.user)

        response = self.client.post(self.url, {
            "old_password": "OldPass123",
            "new_password": "OldPass123",
            "confirm_password": "OldPass123"
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestChangeEmailView:

    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="emailuser",
            email="email@example.com",
            password="Pass123",
            role="user"
        )
        self.client.force_authenticate(self.user)
        self.url = reverse("change_email")

    @patch("users.views.send_mail")
    def test_send_email_otp_success(self, mock_send):
        response = self.client.post(self.url, {
            "email": "email@example.com"
        })

        assert response.status_code == status.HTTP_200_OK
        assert EmailOTP.objects.filter(user=self.user).exists()
        mock_send.assert_called_once()

    def test_email_mismatch(self):
        response = self.client.post(self.url, {
            "email": "wrong@example.com"
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
class TestEmailOTPVerify:

    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="otpuser",
            email="otp@example.com",
            password="Pass123",
            role="user"
        )
        self.client.force_authenticate(self.user)
        self.url = reverse("verify_email")

    def test_verify_valid_otp(self):
        otp = EmailOTP.objects.create(
            user=self.user,
            email=self.user.email,
            otp="123456"
        )

        response = self.client.post(self.url, {
            "otp": "123456"
        })

        assert response.status_code == status.HTTP_200_OK
        assert self.client.session["email_verified"] is True

    def test_invalid_otp(self):
        response = self.client.post(self.url, {
            "otp": "999999"
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
class TestUpdateEmailView:

    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="updateemail",
            email="old@example.com",
            password="Pass123",
            role="user"
        )
        self.client.force_authenticate(self.user)
        self.url = reverse("update_email")

    def test_update_email_without_verification(self):
        response = self.client.post(self.url, {
            "email": "new@example.com"
        })

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_email_success(self):
        session = self.client.session
        session["email_verified"] = True
        session.save()

        response = self.client.post(self.url, {
            "email": "new@example.com"
        })

        assert response.status_code == status.HTTP_200_OK
        self.user.refresh_from_db()
        assert self.user.email == "new@example.com"