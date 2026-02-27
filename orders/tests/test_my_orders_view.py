import pytest
from django.urls import reverse
from rest_framework import status
from django.utils import timezone
from datetime import timedelta

from orders.models import Order
from cart.models import Cart, CartItem


@pytest.mark.django_db
class TestMyOrdersView:

    def test_get_my_orders_success(self, api_client, user, product):
        # create cart + cart item
        cart = Cart.objects.create(user=user)
        cart_item = CartItem.objects.create(
            cart=cart,
            build_name="Test Build",
            cpu=product,
            total_price=10000
        )

        # create order
        Order.objects.create(
            user=user,
            cart_item=cart_item,
            total_price=10000,
            status="PAYMENT_PENDING"
        )

        api_client.force_authenticate(user=user)
        url = reverse("my-orders")  # adjust name if needed

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["total_price"] == "10000.00"
        assert response.data[0]["status"] == "PAYMENT_PENDING"

    def test_orders_only_for_authenticated_user(self, api_client, user, worker, product):
        # user order
        cart1 = Cart.objects.create(user=user)
        cart_item1 = CartItem.objects.create(cart=cart1, cpu=product, total_price=10000)
        Order.objects.create(user=user, cart_item=cart_item1, total_price=10000)

        # another user's order
        cart2 = Cart.objects.create(user=worker)
        cart_item2 = CartItem.objects.create(cart=cart2, cpu=product, total_price=20000)
        Order.objects.create(user=worker, cart_item=cart_item2, total_price=20000)

        api_client.force_authenticate(user=user)
        url = reverse("my-orders")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["total_price"] == "10000.00"

    def test_orders_ordered_newest_first(self, api_client, user, product):
        cart = Cart.objects.create(user=user)

        old_item = CartItem.objects.create(cart=cart, cpu=product, total_price=10000)
        new_item = CartItem.objects.create(cart=cart, cpu=product, total_price=20000)

        old_order = Order.objects.create(user=user, cart_item=old_item, total_price=10000)
        new_order = Order.objects.create(user=user, cart_item=new_item, total_price=20000)

        # 🔧 fix timestamps for deterministic ordering
        Order.objects.filter(id=old_order.id).update(
            created_at=timezone.now() - timedelta(minutes=5)
        )
        Order.objects.filter(id=new_order.id).update(
            created_at=timezone.now()
        )

        api_client.force_authenticate(user=user)
        url = reverse("my-orders")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data[0]["total_price"] == "20000.00"
        assert response.data[1]["total_price"] == "10000.00"

    def test_empty_orders(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse("my-orders")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    def test_unauthenticated_access(self, api_client):
        url = reverse("my-orders")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN