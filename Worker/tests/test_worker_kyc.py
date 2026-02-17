import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from Worker.models import WorkerKycProgress
import uuid
from Worker.models import (
    WorkerIdentityKYC,
    WorkerPayoutDetails,
)

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

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def create_user():
    def _create_user(**kwargs):
        uid = uuid.uuid4().hex[:8]
        return User.objects.create_user(
            email=f"user_{uid}@example.com",
            username=f"user_{uid}",
            password="password123",
            role=kwargs.get("role", "user"),
        )
    return _create_user


@pytest.fixture
def create_worker(create_user):
    def _create_worker():
        worker = create_user(role="worker")
        profile = worker.worker_profile
        profile.kyc_status = "started"
        profile.save()
        return worker
    return _create_worker

@pytest.mark.django_db
class TestWorkerIdentityKYCAPIView:

    def test_get_kyc_not_found(self, api_client, create_worker):
        worker = create_worker()
        api_client.force_authenticate(user=worker)

        url = reverse("worker-verification-update")
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data["detail"] == "Identity KYC not found"

    def test_create_kyc(self, api_client, create_worker):
        worker = create_worker()
        api_client.force_authenticate(user=worker)

        url = reverse("worker-verification-update")

        payload = {
            "id_type": "aadhaar",
            "id_number": "123412341234",
            "id_front_url": "https://img.com/front.jpg",
            "id_front_id": "front_1",
        }

        response = api_client.post(url, payload, format="json")

        assert response.status_code == 200
        assert response.data["message"] == "Identity KYC saved successfully"
        assert WorkerIdentityKYC.objects.count() == 1

    def test_get_kyc_success(self, api_client, create_worker):
        worker = create_worker()

        WorkerIdentityKYC.objects.create(
            user=worker,
            id_type="aadhaar",
            id_number="123412341234",
            id_front_url="https://img.com/front.jpg",
            id_front_id="front_1",
        )

        api_client.force_authenticate(user=worker)

        url = reverse("worker-verification-update")
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data["id_type"] == "aadhaar"

    def test_update_kyc(self, api_client, create_worker):
        worker = create_worker()

        WorkerIdentityKYC.objects.create(
            user=worker,
            id_type="aadhaar",
            id_number="123412341234",
            id_front_url="https://img.com/front.jpg",
            id_front_id="front_1",
        )

        api_client.force_authenticate(user=worker)

        url = reverse("worker-verification-update")

        payload = {
            "id_type": "pan",
            "id_number": "ABCDE1234F",
            "id_front_url": "https://img.com/new.jpg",
            "id_front_id": "front_2",
        }

        response = api_client.post(url, payload, format="json")

        assert response.status_code == 200
        assert WorkerIdentityKYC.objects.count() == 1

    def test_kyc_validation_error(self, api_client, create_worker):
        worker = create_worker()
        api_client.force_authenticate(user=worker)

        url = reverse("worker-verification-update")

        payload = {
            "id_type": "aadhaar"
            # missing required fields
        }

        response = api_client.post(url, payload, format="json")

        assert response.status_code == 400

    def test_kyc_unauthenticated(self, api_client):
        url = reverse("worker-verification-update")
        response = api_client.get(url)

        assert response.status_code in (401, 403)

@pytest.mark.django_db
class TestWorkerPayoutAPIView:

    def test_get_payout_not_found(self, api_client, create_worker):
        worker = create_worker()
        api_client.force_authenticate(user=worker)

        url = reverse("worker-Payout")
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data["upi_id"] is None

    def test_create_payout(self, api_client, create_worker):
        worker = create_worker()
        api_client.force_authenticate(user=worker)

        url = reverse("worker-Payout")

        response = api_client.post(url, {"upi_id": "name@upi"}, format="json")

        assert response.status_code == 200
        assert response.data["message"] == "UPI saved successfully"
        assert WorkerPayoutDetails.objects.count() == 1

    def test_update_payout(self, api_client, create_worker):
        worker = create_worker()

        WorkerPayoutDetails.objects.create(user=worker, upi_id="old@upi")

        api_client.force_authenticate(user=worker)

        url = reverse("worker-Payout")
        response = api_client.post(url, {"upi_id": "new@upi"}, format="json")

        assert response.status_code == 200
        payout = WorkerPayoutDetails.objects.get(user=worker)
        assert payout.upi_id == "new@upi"

    def test_invalid_upi(self, api_client, create_worker):
        worker = create_worker()
        api_client.force_authenticate(user=worker)

        url = reverse("worker-Payout")

        response = api_client.post(url, {"upi_id": ""}, format="json")

        assert response.status_code == 400

    def test_payout_unauthenticated(self, api_client):
        url = reverse("worker-Payout")
        response = api_client.get(url)

        assert response.status_code in (401, 403)

@pytest.mark.django_db
class TestWorkerKycStatusChangeAPIView:

    def test_submit_kyc_success(self, api_client, create_worker):
        worker = create_worker()
        api_client.force_authenticate(user=worker)

        url = reverse("chat-request-action")
        response = api_client.post(url)

        assert response.status_code == 200
        assert response.data["kyc_status"] == "pending"

        worker.worker_profile.refresh_from_db()
        assert worker.worker_profile.kyc_status == "pending"

    def test_worker_profile_not_found(self, api_client, create_user):
        user = create_user(role="user")  # not worker
        api_client.force_authenticate(user=user)

        url = reverse("chat-request-action")
        response = api_client.post(url)

        assert response.status_code == 404
        assert response.data["error"] == "invalid user"

    def test_kyc_submit_unauthenticated(self, api_client):
        url = reverse("chat-request-action")
        response = api_client.post(url)

        assert response.status_code in (401, 403)