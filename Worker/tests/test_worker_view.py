import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from Worker.models import ChatRequest 
from Authentication.models import User,WorkerProfile


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def create_user():
    def _create_user(**kwargs):
        return User.objects.create_user(
            email=kwargs.get("email", "user@example.com"),
            username=kwargs.get("username", "testuser"),
            password=kwargs.get("password", "password123"),
            role=kwargs.get("role", "user"),
        )
    return _create_user



@pytest.fixture
def create_worker(create_user):
    def _create_worker(**kwargs):
        worker_user = create_user(
            email=kwargs.get("email", "worker@example.com"),
            username=kwargs.get("username", "workeruser"),
            role="worker",
        )

        worker_profile = worker_user.worker_profile

        worker_profile.skills = "Electrician"
        worker_profile.hourly_rate = 500
        worker_profile.rating = 4.5

        # 🔥 THIS IS THE REAL FIX
        worker_profile.kyc_status = "approved"

        worker_profile.save()

        return worker_user, worker_profile

    return _create_worker

@pytest.mark.django_db
class TestWorkerListAPIView:

    def test_worker_list_no_request(self, api_client, create_user, create_worker):
        user = create_user()
        api_client.force_authenticate(user=user)

        worker_user, worker_profile = create_worker()

        url = reverse("worker-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

        worker_data = response.data[0]
        assert worker_data["user_id"] == worker_user.id
        assert worker_data["skills"] == "Electrician"
        assert worker_data["hourly_rate"] == "500.00"
        assert worker_data["has_requested"] is False

    def test_worker_list_with_pending_request(self, api_client, create_user, create_worker):
        user = create_user()
        api_client.force_authenticate(user=user)

        worker_user, worker_profile = create_worker()

        ChatRequest.objects.create(
            sender=user,
            receiver=worker_user,
            status="pending",
        )

        url = reverse("worker-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        worker_data = response.data[0]
        assert worker_data["has_requested"] is True

    def test_worker_list_unauthenticated(self, api_client):
        url = reverse("worker-list")
        response = api_client.get(url)

        assert response.status_code in (401, 403)

@pytest.mark.django_db
class TestWorkerDetailsView:

    def test_update_worker_details_success(self, api_client, create_worker):
        worker_user, worker_profile = create_worker()
        api_client.force_authenticate(user=worker_user)

        url = reverse("worker-details-update")

        payload = {
            "description": "Experienced electrician",
            "skills": "Wiring, Installation",
            "experience_years": 5,
            "hourly_rate": 600,
        }

        response = api_client.patch(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK

        # DRF UpdateAPIView returns updated object
        assert response.data["description"] == "Experienced electrician"
        assert response.data["skills"] == "Wiring, Installation"
        assert response.data["experience_years"] == 5
        assert response.data["hourly_rate"] == "600.00"

        # DB validation
        worker_profile.refresh_from_db()
        assert worker_profile.description == "Experienced electrician"
        assert worker_profile.skills == "Wiring, Installation"
        assert worker_profile.experience_years == 5
        assert str(worker_profile.hourly_rate) == "600.00"

    def test_partial_update_worker_details(self, api_client, create_worker):
        worker_user, worker_profile = create_worker()
        api_client.force_authenticate(user=worker_user)

        url = reverse("worker-details-update")

        payload = {
            "skills": "Solar installation"
        }

        response = api_client.patch(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK

        worker_profile.refresh_from_db()
        assert worker_profile.skills == "Solar installation"

    def test_worker_profile_not_found(self, api_client, create_user):
        user = create_user(role="user")
        api_client.force_authenticate(user=user)

        url = reverse("worker-details-update")
        response = api_client.patch(url, {"skills": "Test"}, format="json")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data["detail"] == "Worker profile not found"

    def test_validation_error(self, api_client, create_worker):
        worker_user, worker_profile = create_worker()
        api_client.force_authenticate(user=worker_user)

        url = reverse("worker-details-update")

        payload = {
            "experience_years": "invalid"  # should be integer
        }

        response = api_client.patch(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_worker_details_unauthenticated(self, api_client):
        url = reverse("worker-details-update")
        response = api_client.patch(url, {"skills": "Test"}, format="json")

        assert response.status_code in (401, 403)
