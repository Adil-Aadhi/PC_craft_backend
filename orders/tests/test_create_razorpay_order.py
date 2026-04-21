import pytest
from django.urls import reverse
from rest_framework import status
from unittest.mock import patch
import hmac
import hashlib
from django.conf import settings
from orders.models import Order
from orders.models import Payment
import uuid

from cart.models import Cart, CartItem


@pytest.mark.django_db
class TestCreateRazorpayOrderView:

    @patch("orders.views.client.order.create")
    def test_create_razorpay_order_success(
        self, mock_create, api_client, user, product
    ):
        # mock razorpay response
        mock_create.return_value = {
            "id": "order_test_123"
        }
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
        url = reverse("create-razorpay")

        response = api_client.post(url, {
            "order_id": str(order.order_id)
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data["razorpay_order_id"] == "order_test_123"
        assert response.data["amount"] == 100000  # 1000 * 100

        # check payment created
        payment = Payment.objects.get(order=order)
        assert payment.status == "CREATED"
        assert payment.razorpay_order_id == "order_test_123"


    def test_missing_order_id(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse("create-razorpay")

        response = api_client.post(url, {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.data


    def test_order_not_found(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse("create-razorpay")

        response = api_client.post(url, {
            "order_id": str(uuid.uuid4())  # valid UUID, not in DB
        })

        assert response.status_code == status.HTTP_404_NOT_FOUND


    def test_order_not_belongs_to_user(
        self, api_client, user, worker
    ):
        
        cart = Cart.objects.create(user=user)

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
        url = reverse("create-razorpay")

        response = api_client.post(url, {
            "order_id": str(order.order_id)
        })

        assert response.status_code == status.HTTP_404_NOT_FOUND


    def test_order_already_paid(self, api_client, user):

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
        url = reverse("create-razorpay")

        response = api_client.post(url, {
            "order_id": str(order.order_id)
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST


    def test_unauthenticated_access(self, api_client):
        url = reverse("create-razorpay")

        response = api_client.post(url, {
            "order_id": "anything"
        })

        assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.django_db
class TestVerifyRazorpayPaymentView:

    def generate_signature(self, order_id, payment_id):
        body = f"{order_id}|{payment_id}"
        return hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode(),
            body.encode(),
            hashlib.sha256
        ).hexdigest()

    def setup_payment(self, user):
        cart = Cart.objects.create(user=user)
        cart_item = CartItem.objects.create(cart=cart, total_price=1000)

        order = Order.objects.create(
            user=user,
            cart_item=cart_item,
            total_price=1000,
            status="PAYMENT_PENDING"
        )

        payment = Payment.objects.create(
            order=order,
            amount=1000,
            currency="INR",
            status="CREATED",
            razorpay_order_id="order_test_123"
        )

        return order, payment

    @patch("orders.views.generate_invoice")
    @patch("orders.views.create_order_progress")
    def test_verify_payment_success(
        self, mock_progress, mock_invoice, api_client, user
    ):
        order, payment = self.setup_payment(user)

        mock_invoice.return_value = "invoice.pdf"

        signature = self.generate_signature(
            payment.razorpay_order_id,
            "pay_123"
        )

        api_client.force_authenticate(user=user)
        url = reverse("verify-razorpay")

        response = api_client.post(url, {
            "razorpay_order_id": payment.razorpay_order_id,
            "razorpay_payment_id": "pay_123",
            "razorpay_signature": signature
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "Payment successful"

        payment.refresh_from_db()
        order.refresh_from_db()

        assert payment.status == "SUCCESS"
        assert order.status == "CONFIRMED"
        assert payment.razorpay_payment_id == "pay_123"

    def test_missing_fields(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse("verify-razorpay")

        response = api_client.post(url, {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_payment_not_found(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse("verify-razorpay")

        response = api_client.post(url, {
            "razorpay_order_id": "order_fake",
            "razorpay_payment_id": "pay_123",
            "razorpay_signature": "abc"
        })

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_invalid_signature(self, api_client, user):
        order, payment = self.setup_payment(user)

        api_client.force_authenticate(user=user)
        url = reverse("verify-razorpay")

        response = api_client.post(url, {
            "razorpay_order_id": payment.razorpay_order_id,
            "razorpay_payment_id": "pay_123",
            "razorpay_signature": "wrong_signature"
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        payment.refresh_from_db()
        assert payment.status == "FAILED"

    def test_already_paid(self, api_client, user):
        order, payment = self.setup_payment(user)

        payment.status = "SUCCESS"
        payment.save()

        api_client.force_authenticate(user=user)
        url = reverse("verify-razorpay")

        response = api_client.post(url, {
            "razorpay_order_id": payment.razorpay_order_id,
            "razorpay_payment_id": "pay_123",
            "razorpay_signature": "anything"
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "Already paid"

    @patch("orders.views.generate_invoice")
    @patch("orders.views.create_order_progress")
    def test_order_not_pending(self, mock_progress, mock_invoice, api_client, user):
        order, payment = self.setup_payment(user)

        order.status = "CONFIRMED"
        order.save()

        signature = self.generate_signature(
            payment.razorpay_order_id,
            "pay_123"
        )

        api_client.force_authenticate(user=user)
        url = reverse("verify-razorpay")

        response = api_client.post(url, {
            "razorpay_order_id": payment.razorpay_order_id,
            "razorpay_payment_id": "pay_123",
            "razorpay_signature": signature
        })

        assert response.status_code == status.HTTP_200_OK

        payment.refresh_from_db()
        order.refresh_from_db()

        assert payment.status == "SUCCESS"
        assert order.status == "CONFIRMED"  # unchanged

    def test_unauthenticated(self, api_client):
        url = reverse("verify-razorpay")

        response = api_client.post(url, {})

        assert response.status_code == status.HTTP_403_FORBIDDEN