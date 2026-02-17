import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


@pytest.fixture
def api_client():
    client = APIClient()
    client.defaults["HTTP_ACCEPT"] = "application/json"
    return client


@pytest.fixture
def create_user():
    def _create_user(**kwargs):
        return User.objects.create_user(
            email=kwargs.get("email", "test@example.com"),
            username=kwargs.get("username", "testuser"),
            password=kwargs.get("password", "password123"),
            role=kwargs.get("role", "user"),  # 🔴 required in your model
        )
    return _create_user


@pytest.mark.django_db
class TestMeAPIView:

    def test_me_authenticated(self, api_client, create_user):
        user = create_user()

        api_client.force_authenticate(user=user)

        # 🔁 Use your real endpoint path here
        url = reverse("auth-me")

        response = api_client.get(url, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == user.id
        assert response.data["email"] == user.email
        assert response.data["username"] == user.username

    def test_me_unauthenticated(self, api_client):
        url = reverse("auth-me")
        response = api_client.get(url, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN
