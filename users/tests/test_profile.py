import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import io

User = get_user_model()

def generate_test_image():
    file = io.BytesIO()
    image = Image.new("RGB", (100, 100), color="red")
    image.save(file, "JPEG")
    file.seek(0)
    return SimpleUploadedFile(
        "test.jpg",
        file.read(),
        content_type="image/jpeg"
    )

@pytest.mark.django_db
class TestProfileView:

    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="profileuser",
            email="profile@example.com",
            password="StrongPass123",
            role="user"
        )
        self.url = reverse("profile")  # ensure URL name is correct

    def test_get_profile_authenticated(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert "full_name" in response.data

    def test_get_profile_unauthenticated(self):
        response = self.client.get(self.url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_patch_profile_success(self):
        self.client.force_authenticate(user=self.user)

        data = {
            "full_name": "Updated Name"
        }

        response = self.client.patch(self.url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["full_name"] == "Updated Name"

    def test_patch_profile_invalid_data(self):
        self.client.force_authenticate(user=self.user)

        data = {
            "date_of_birth": "invalid-date"
        }

        response = self.client.patch(self.url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
class TestUpdateProfileImage:

    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="imguser",
            email="img@example.com",
            password="StrongPass123",
            role="user"
        )
        self.url = reverse("update_image")  # make sure URL name matches


    @patch("users.views.cloudinary.uploader.destroy")
    def test_delete_profile_image_success(self, mock_destroy):
        self.client.force_authenticate(user=self.user)

        profile = self.user.user_profile
        profile.profile_image_id = "cloudinary_id_123"
        profile.save()

        response = self.client.delete(self.url)

        assert response.status_code == status.HTTP_200_OK
        mock_destroy.assert_called_once_with("cloudinary_id_123")