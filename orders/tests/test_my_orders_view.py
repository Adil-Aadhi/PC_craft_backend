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

@pytest.mark.django_db
class TestCancelOrderView:

    def test_cancel_order_success(self, api_client, user):
        # create cart + cart item
        cart = Cart.objects.create(user=user)
        cart_item = CartItem.objects.create(
            cart=cart,
            total_price=1000
        )

        # create order
        order = Order.objects.create(
            user=user,
            cart_item=cart_item,
            total_price=1000,
            status="PAYMENT_PENDING"
        )

        api_client.force_authenticate(user=user)
        url = reverse("cancel-order", args=[order.order_id])

        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "Order cancelled"

        # verify DB
        order.refresh_from_db()
        assert order.status == "CANCELLED"


    def test_cancel_order_not_found(self, api_client, user):
        import uuid

        api_client.force_authenticate(user=user)
        url = reverse("cancel-order", args=[uuid.uuid4()])

        response = api_client.post(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "error" in response.data


    def test_cancel_order_not_belongs_to_user(self, api_client, user, worker):
        # create order for another user
        cart = Cart.objects.create(user=worker)
        cart_item = CartItem.objects.create(
            cart=cart,
            total_price=1000
        )

        order = Order.objects.create(
            user=worker,
            cart_item=cart_item,
            total_price=1000,
            status="PAYMENT_PENDING"
        )

        api_client.force_authenticate(user=user)
        url = reverse("cancel-order", args=[order.order_id])

        response = api_client.post(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND


    def test_cancel_order_already_paid(self, api_client, user):
        cart = Cart.objects.create(user=user)
        cart_item = CartItem.objects.create(
            cart=cart,
            total_price=1000
        )

        order = Order.objects.create(
            user=user,
            cart_item=cart_item,
            total_price=1000,
            status="PAID"
        )

        api_client.force_authenticate(user=user)
        url = reverse("cancel-order", args=[order.order_id])

        response = api_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Only unpaid orders can be cancelled" in response.data["error"]


    def test_cancel_order_already_cancelled(self, api_client, user):
        cart = Cart.objects.create(user=user)
        cart_item = CartItem.objects.create(
            cart=cart,
            total_price=1000
        )

        order = Order.objects.create(
            user=user,
            cart_item=cart_item,
            total_price=1000,
            status="CANCELLED"
        )

        api_client.force_authenticate(user=user)
        url = reverse("cancel-order", args=[order.order_id])

        response = api_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


    def test_unauthenticated_access(self, api_client, user):
        cart = Cart.objects.create(user=user)
        cart_item = CartItem.objects.create(
            cart=cart,
            total_price=1000
        )

        order = Order.objects.create(
            user=user,
            cart_item=cart_item,
            total_price=1000,
            status="PAYMENT_PENDING"
        )

        url = reverse("cancel-order", args=[order.order_id])

        response = api_client.post(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.django_db
class TestWorkerOrdersView:

    def create_order(self, user, worker, status):
        cart = Cart.objects.create(user=user)
        cart_item = CartItem.objects.create(
            cart=cart,
            total_price=1000
        )

        return Order.objects.create(
            user=user,
            worker=worker,
            cart_item=cart_item,
            total_price=1000,
            status=status
        )

    def test_get_all_orders(self, api_client, user, worker):
        # create orders
        self.create_order(user, worker, "PAYMENT_PENDING")
        self.create_order(user, worker, "BUILD_IN_PROGRESS")
        self.create_order(user, worker, "COMPLETED")

        api_client.force_authenticate(user=worker)
        url = reverse("worker-project")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["orders"]) == 3

        counts = response.data["counts"]
        assert counts["TOTAL"] == 3
        assert counts["PAYMENT_PENDING"] == 1
        assert counts["BUILD_IN_PROGRESS"] == 1
        assert counts["COMPLETED"] == 1

    def test_filter_pending_orders(self, api_client, user, worker):
        self.create_order(user, worker, "PAYMENT_PENDING")
        self.create_order(user, worker, "COMPLETED")

        api_client.force_authenticate(user=worker)
        url = reverse("worker-project")

        response = api_client.get(url, {"status": "pending"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["orders"]) == 1
        assert response.data["orders"][0]["status"] == "PAYMENT_PENDING"

    def test_filter_in_progress_orders(self, api_client, user, worker):
        self.create_order(user, worker, "BUILD_IN_PROGRESS")
        self.create_order(user, worker, "COMPLETED")

        api_client.force_authenticate(user=worker)
        url = reverse("worker-project")

        response = api_client.get(url, {"status": "in_progress"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["orders"]) == 1
        assert response.data["orders"][0]["status"] == "BUILD_IN_PROGRESS"

    def test_filter_completed_orders(self, api_client, user, worker):
        self.create_order(user, worker, "COMPLETED")
        self.create_order(user, worker, "PAYMENT_PENDING")

        api_client.force_authenticate(user=worker)
        url = reverse("worker-project")

        response = api_client.get(url, {"status": "completed"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["orders"]) == 1
        assert response.data["orders"][0]["status"] == "COMPLETED"

    def test_invalid_filter_returns_all(self, api_client, user, worker):
        self.create_order(user, worker, "PAYMENT_PENDING")
        self.create_order(user, worker, "COMPLETED")

        api_client.force_authenticate(user=worker)
        url = reverse("worker-project")

        response = api_client.get(url, {"status": "invalid"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["orders"]) == 2

    def test_orders_only_for_logged_in_worker(self, api_client, user, worker):
        other_worker = user  # simulate another user

        # orders for worker
        self.create_order(user, worker, "PAYMENT_PENDING")

        # orders for another worker
        cart = Cart.objects.create(user=user)
        cart_item = CartItem.objects.create(cart=cart, total_price=1000)

        Order.objects.create(
            user=user,
            worker=other_worker,
            cart_item=cart_item,
            total_price=1000,
            status="COMPLETED"
        )

        api_client.force_authenticate(user=worker)
        url = reverse("worker-project")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["orders"]) == 1

    def test_ordering_newest_first(self, api_client, user, worker):
        order1 = self.create_order(user, worker, "PAYMENT_PENDING")
        order2 = self.create_order(user, worker, "COMPLETED")

        api_client.force_authenticate(user=worker)
        url = reverse("worker-project")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        # newest first
        assert response.data["orders"][0]["id"] == order2.id

    def test_counts_always_correct(self, api_client, user, worker):
        self.create_order(user, worker, "PAYMENT_PENDING")
        self.create_order(user, worker, "PAYMENT_PENDING")
        self.create_order(user, worker, "COMPLETED")

        api_client.force_authenticate(user=worker)
        url = reverse("worker-project")

        response = api_client.get(url, {"status": "pending"})

        counts = response.data["counts"]

        # counts should be from full dataset (not filtered)
        assert counts["TOTAL"] == 3
        assert counts["PAYMENT_PENDING"] == 2
        assert counts["COMPLETED"] == 1

    def test_unauthenticated(self, api_client):
        url = reverse("worker-project")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.django_db
class TestWorkerOrderDetailView:

    def create_order(self, user, worker, status="PAYMENT_PENDING"):
        cart = Cart.objects.create(user=user)
        cart_item = CartItem.objects.create(
            cart=cart,
            total_price=1000
        )

        return Order.objects.create(
            user=user,
            worker=worker,
            cart_item=cart_item,
            total_price=1000,
            status=status
        )

    def test_get_order_detail_success(self, api_client, user, worker):
        order = self.create_order(user, worker)

        api_client.force_authenticate(user=worker)
        url = reverse("worker-project-individual", args=[order.order_id])

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == order.id
        assert response.data["order_id"] == str(order.order_id)
        assert response.data["status"] == order.status
        assert response.data["total_price"] == "1000.00"
        assert response.data["username"] == user.username

    def test_worker_cannot_access_others_order(self, api_client, user, worker):
        other_worker = user  # simulate different user

        order = self.create_order(user, other_worker)

        api_client.force_authenticate(user=worker)
        url = reverse("worker-project-individual", args=[order.order_id])

        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_order_not_found(self, api_client, worker):
        import uuid

        api_client.force_authenticate(user=worker)
        url = reverse("worker-project-individual", args=[uuid.uuid4()])

        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_unauthenticated_access(self, api_client, user, worker):
        order = self.create_order(user, worker)

        url = reverse("worker-project-individual", args=[order.order_id])

        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN