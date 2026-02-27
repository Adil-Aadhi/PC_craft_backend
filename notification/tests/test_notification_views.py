import pytest
from django.urls import reverse
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from notification.models import FCMToken, Notification


@pytest.mark.django_db
class TestSaveFCMTokenAPIView:

    def test_save_fcm_token_success(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse("notification:notification-savetoken")  # adjust if name different

        payload = {"fcm_token": "test_fcm_token_123"}

        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["message"] == "FCM token saved"

        assert FCMToken.objects.filter(user=user, token="test_fcm_token_123").exists()

    def test_update_existing_fcm_token(self, api_client, user):
        FCMToken.objects.create(user=user, token="old_token")

        api_client.force_authenticate(user=user)
        url = reverse("notification:notification-savetoken")

        payload = {"fcm_token": "new_token"}

        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK

        token_obj = FCMToken.objects.get(user=user)
        assert token_obj.token == "new_token"

    def test_missing_token(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse("notification:notification-savetoken")

        response = api_client.post(url, {}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["error"] == "Token required"

    def test_unauthenticated_user(self, api_client):
        url = reverse("notification:notification-savetoken")

        response = api_client.post(url, {"fcm_token": "abc"}, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.django_db
class TestWorkerNotificationListAPIView:

    def test_get_notifications(self, api_client, user):
        Notification.objects.create(
            user=user,
            title="Test Title",
            message="Test Message",
            is_read=False
        )

        api_client.force_authenticate(user=user)
        url = reverse("notification:notificaton-worker-listout") 

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["title"] == "Test Title"
        assert response.data[0]["is_read"] is False

    def test_notifications_ordered_newest_first(self, api_client, user):
        old_notification = Notification.objects.create(
            user=user,
            title="Old",
            message="Old message"
        )

        new_notification = Notification.objects.create(
            user=user,
            title="New",
            message="New message"
        )

        # 🔧 manually override timestamps AFTER creation
        Notification.objects.filter(id=old_notification.id).update(
            created_at=timezone.now() - timedelta(minutes=5)
        )

        Notification.objects.filter(id=new_notification.id).update(
            created_at=timezone.now()
        )

        api_client.force_authenticate(user=user)
        url = reverse("notification:notificaton-worker-listout")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data[0]["title"] == "New"
        assert response.data[1]["title"] == "Old"
    def test_empty_notifications(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse("notification:notificaton-worker-listout")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    def test_unauthenticated_access(self, api_client):
        url = reverse("notification:notificaton-worker-listout")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN