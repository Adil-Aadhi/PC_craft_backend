import pytest
import uuid
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from unittest.mock import patch
from Authentication.models import User, WorkerProfile
from Worker.models import ChatRequest, ChatRoom, ChatMessage


@pytest.fixture
def api_client():
    return APIClient()




@pytest.fixture
def create_user():
    def _create_user(**kwargs):
        unique_id = uuid.uuid4().hex[:8]

        return User.objects.create_user(
            email=kwargs.get("email", f"user_{unique_id}@example.com"),
            username=kwargs.get("username", f"user_{unique_id}"),
            password="password123",
            role=kwargs.get("role", "user"),
        )
    return _create_user

@pytest.fixture
def create_worker(create_user):
    def _create_worker(**kwargs):
        worker_user = create_user(role="worker")

        # profile auto-created by signal
        profile = worker_user.worker_profile
        profile.skills = "Electrician"
        profile.save()

        return worker_user

    return _create_worker

@pytest.mark.django_db
class TestChatRequestCreateAPIView:

    def test_send_chat_request_success(self, api_client, create_user, create_worker):
        sender = create_user()
        worker = create_worker()

        api_client.force_authenticate(user=sender)

        url = reverse("chat-request-create")
        response = api_client.post(url, {"receiver_id": worker.id}, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == "pending"
        assert ChatRequest.objects.count() == 1

    def test_cannot_send_to_self(self, api_client, create_user):
        user = create_user()
        api_client.force_authenticate(user=user)

        url = reverse("chat-request-create")
        response = api_client.post(url, {"receiver_id": user.id}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cannot_send_to_non_worker(self, api_client, create_user):
        sender = create_user()
        normal_user = create_user()

        api_client.force_authenticate(user=sender)

        url = reverse("chat-request-create")
        response = api_client.post(url, {"receiver_id": normal_user.id}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_duplicate_pending_request(self, api_client, create_user, create_worker):
        sender = create_user()
        worker = create_worker()

        ChatRequest.objects.create(
            sender=sender,
            receiver=worker,
            status="pending"
        )

        api_client.force_authenticate(user=sender)

        url = reverse("chat-request-create")
        response = api_client.post(url, {"receiver_id": worker.id}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_unauthenticated(self, api_client, create_worker):
        worker = create_worker()

        url = reverse("chat-request-create")
        response = api_client.post(url, {"receiver_id": worker.id}, format="json")

        assert response.status_code in (401, 403)

@pytest.mark.django_db
class TestChatRequestActionAPIView:

    @patch("Worker.views.ChatMessage.objects.create")
    def test_accept_request_creates_room_and_message(
        self, mock_create, api_client, create_user, create_worker
    ):
        sender = create_user()
        worker = create_worker()

        chat_request = ChatRequest.objects.create(
            sender=sender,
            receiver=worker,
            status="pending"
        )

        api_client.force_authenticate(user=worker)

        url = reverse("chat-request-action", args=[chat_request.id])
        response = api_client.patch(url, {"status": "accepted"}, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["room_created"] is True

        chat_request.refresh_from_db()
        assert chat_request.status == "accepted"

        # ✅ Room created
        assert ChatRoom.objects.count() == 1

        room = ChatRoom.objects.first()
        assert sender in room.participants.all()
        assert worker in room.participants.all()

        # ✅ Message creation was called (mocked)
        mock_create.assert_called_once()

    def test_reject_request(self, api_client, create_user, create_worker):
        sender = create_user()
        worker = create_worker()

        chat_request = ChatRequest.objects.create(
            sender=sender,
            receiver=worker,
            status="pending"
        )

        api_client.force_authenticate(user=worker)

        url = reverse("chat-request-action", args=[chat_request.id])
        response = api_client.patch(url, {"status": "rejected"}, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["room_created"] is False

        chat_request.refresh_from_db()
        assert chat_request.status == "rejected"
        assert ChatRoom.objects.count() == 0

    def test_non_receiver_cannot_act(self, api_client, create_user, create_worker):
        sender = create_user()
        worker = create_worker()
        other_user = create_user()

        chat_request = ChatRequest.objects.create(
            sender=sender,
            receiver=worker,
            status="pending"
        )

        api_client.force_authenticate(user=other_user)

        url = reverse("chat-request-action", args=[chat_request.id])
        response = api_client.patch(url, {"status": "accepted"}, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_request_not_found(self, api_client, create_user):
        user = create_user()
        api_client.force_authenticate(user=user)

        url = reverse("chat-request-action", args=[999])
        response = api_client.patch(url, {"status": "accepted"}, format="json")

        assert response.status_code == 404

    def test_already_handled(self, api_client, create_user, create_worker):
        sender = create_user()
        worker = create_worker()

        chat_request = ChatRequest.objects.create(
            sender=sender,
            receiver=worker,
            status="accepted"
        )

        api_client.force_authenticate(user=worker)

        url = reverse("chat-request-action", args=[chat_request.id])
        response = api_client.patch(url, {"status": "rejected"}, format="json")

        assert response.status_code == 400
        assert response.data["detail"] == "Already handled"

    def test_unauthenticated(self, api_client, create_user, create_worker):
        sender = create_user()
        worker = create_worker()

        chat_request = ChatRequest.objects.create(
            sender=sender,
            receiver=worker,
            status="pending"
        )

        url = reverse("chat-request-action", args=[chat_request.id])
        response = api_client.patch(url, {"status": "accepted"}, format="json")

        assert response.status_code in (401, 403)
