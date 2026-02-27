import pytest
from django.urls import reverse
from rest_framework import status

from cart.models import Cart, CartItem


@pytest.mark.django_db
class TestUpdateCartItemView:

    def test_get_single_cart_item(self, api_client, user, product):
        cart = Cart.objects.create(user=user)
        item = CartItem.objects.create(cart=cart, build_name="Test Build", cpu=product)

        api_client.force_authenticate(user=user)
        url = reverse("cart-delete", args=[item.id])

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == item.id

    def test_patch_cart_item(self, api_client, user, product):
        cart = Cart.objects.create(user=user)
        item = CartItem.objects.create(cart=cart, build_name="Old Build", cpu=product)

        api_client.force_authenticate(user=user)
        url = reverse("cart-delete", args=[item.id])

        payload = {"build_name": "Updated Build"}

        response = api_client.patch(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["message"] == "Build updated successfully"

        item.refresh_from_db()
        assert item.build_name == "Updated Build"

    def test_delete_cart_item(self, api_client, user, product):
        cart = Cart.objects.create(user=user)
        item = CartItem.objects.create(cart=cart, build_name="Delete Build", cpu=product)

        api_client.force_authenticate(user=user)
        url = reverse("cart-delete", args=[item.id])

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_200_OK
        assert CartItem.objects.filter(id=item.id).exists() is False