import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from Authentication.models import WorkerProfile

User = get_user_model()

@pytest.mark.django_db
class TestWorkerProfileImageView:

    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="worker2",
            email="worker2@test.com",
            password="Pass123",
            role="worker"
        )
        self.worker = self.user.worker_profile
        self.client.force_authenticate(self.user)
        self.url = reverse("update_worker_profile")

    def test_get_worker_profile_image_success(self):
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK

    def test_worker_profile_not_found(self):
        WorkerProfile.objects.filter(user=self.user).delete()

        response = self.client.get(self.url)

        assert response.status_code == status.HTTP_200_OK

@pytest.mark.django_db
class TestWorkerPersonalInfoView:

    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="worker2",
            email="worker2@test.com",
            password="Pass123",
            role="worker"
        )
        self.worker = self.user.worker_profile   # ✅ use existing
        self.client.force_authenticate(self.user)
        self.url = reverse("worker-personal-info")

    def test_get_personal_info(self):
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK

    def test_patch_personal_info(self):
        response = self.client.patch(self.url, {
            "full_name": "Updated Worker"
        })
        assert response.status_code == status.HTTP_200_OK

    def test_personal_info_worker_not_found(self):
        self.user.worker_profile.delete()
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK

@pytest.mark.django_db
class TestWorkerBannerImageView:

    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="worker3",
            email="worker3@test.com",
            password="Pass123",
            role="worker"
        )
        self.worker = self.user.worker_profile   # ✅ use existing
        self.client.force_authenticate(self.user)
        self.url = reverse("worker-banner-image")

    def test_get_banner_image(self):
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK

    def test_banner_image_worker_not_found(self):
        self.user.worker_profile.delete()
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK

@pytest.mark.django_db
def test_worker_profile_image_unauthenticated():
    client = APIClient()
    url = reverse("update_worker_profile")

    response = client.get(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN