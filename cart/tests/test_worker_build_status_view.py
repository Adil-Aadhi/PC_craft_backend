import pytest
from django.urls import reverse
from rest_framework import status

from cart.models import Cart, CartItem
from orders.models import Order
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def worker():
    return User.objects.create_user(
        username="worker",
        email="worker@example.com",
        password="StrongPass123!",
        role="worker"
    )


@pytest.mark.django_db
class TestUpdateBuildStatusView:

    def test_only_worker_allowed(self, api_client, user, product):
        cart = Cart.objects.create(user=user)
        item = CartItem.objects.create(cart=cart, build_name="Test Build", cpu=product)

        api_client.force_authenticate(user=user)  # normal user
        url = reverse("cart-status", args=[item.id])

        response = api_client.post(url, {"status": "accepted"}, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_worker_accept_build_creates_order(self, api_client, worker, user, product):
        cart = Cart.objects.create(user=user)
        item = CartItem.objects.create(cart=cart, build_name="Test Build", cpu=product, total_price=10000)

        api_client.force_authenticate(user=worker)
        url = reverse("cart-status", args=[item.id])

        response = api_client.post(url, {"status": "accepted"}, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "accepted"
        assert Order.objects.filter(cart_item=item).exists()

    def test_worker_reject_build(self, api_client, worker, user, product):
        cart = Cart.objects.create(user=user)
        item = CartItem.objects.create(cart=cart, build_name="Test Build", cpu=product)

        api_client.force_authenticate(user=worker)
        url = reverse("cart-status", args=[item.id])

        response = api_client.post(url, {"status": "rejected"}, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "rejected"

    def test_prevent_reprocessing(self, api_client, worker, user, product):
        cart = Cart.objects.create(user=user)
        item = CartItem.objects.create(
            cart=cart,
            build_name="Test Build",
            cpu=product,
            status="accepted"
        )

        api_client.force_authenticate(user=worker)
        url = reverse("cart-status", args=[item.id])

        response = api_client.post(url, {"status": "accepted"}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST