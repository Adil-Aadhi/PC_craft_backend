import pytest
from django.urls import reverse
from rest_framework import status

from cart.models import Cart, CartItem


@pytest.mark.django_db
class TestCartItemSummaryView:

    def test_get_summary(self, api_client, user, product):
        cart = Cart.objects.create(user=user)
        item = CartItem.objects.create(
            cart=cart,
            build_name="Summary Build",
            cpu=product,
            total_price=50000,
            status="active"
        )

        api_client.force_authenticate(user=user)
        url = reverse("cart-summary", args=[item.id])

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["build_name"] == "Summary Build"
        assert response.data["total_price"] == 50000