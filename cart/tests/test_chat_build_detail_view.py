import pytest
from django.urls import reverse
from rest_framework import status

from cart.models import Cart, CartItem


@pytest.mark.django_db
class TestChatBuildDetailView:

    def test_get_chat_build_detail(self, api_client, user, product):
        cart = Cart.objects.create(user=user)
        item = CartItem.objects.create(cart=cart, build_name="Chat Build", cpu=product)

        api_client.force_authenticate(user=user)
        url = reverse("cart-build-chat", args=[item.id])

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == item.id