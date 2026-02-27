import pytest
from django.urls import reverse
from rest_framework import status

from cart.models import Cart, CartItem


@pytest.mark.django_db
class TestCartView:

    def test_get_empty_cart(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse("cart-item")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["items"] == []

    def test_add_build_to_cart(self, api_client, user, product):
        api_client.force_authenticate(user=user)
        url = reverse("cart-item")

        payload = {
            "build_name": "Gaming Build",
            "cpu": product.id   # ✅ use fixture
        }

        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["message"] == "Build added to cart"
        assert CartItem.objects.filter(cart__user=user).count() == 1

    def test_get_cart_with_items(self, api_client, user, product):
        cart = Cart.objects.create(user=user)

        CartItem.objects.create(
            cart=cart,
            build_name="Test Build",
            cpu=product,   # ✅ use fixture
            total_price=product.price
        )

        api_client.force_authenticate(user=user)
        url = reverse("cart-item")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["items"]) == 1