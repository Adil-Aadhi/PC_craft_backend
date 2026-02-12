import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from Worker.models import WorkerKycProgress

User = get_user_model()

@pytest.mark.django_db
class TestWorkerKycProgressView:

    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="worker4",
            email="worker4@test.com",
            password="Pass123",
            role="worker"
        )
        self.client.force_authenticate(self.user)
        self.url = reverse("worker-kyc-progress")

    def test_get_kyc_progress_creates_object(self):
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert WorkerKycProgress.objects.filter(worker=self.user).exists()

    def test_update_kyc_progress(self):
        response = self.client.post(self.url, {
            "current_step": 2,
            "status": "in_progress"
        })
        assert response.status_code == status.HTTP_200_OK

    def test_invalid_kyc_progress_data(self):
        response = self.client.post(self.url, {
            "current_step": 99
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_kyc_unauthenticated_access(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
