from django.shortcuts import render
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import Order,Payment
from .serializers import OrderSerializer,WorkerReviewSerializer
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import razorpay
import hmac
import hashlib
from django.utils.timezone import now
from django.db import transaction
from orders.utils.generate_invoice import generate_invoice
from django.shortcuts import get_object_or_404
from .dynamodb import create_order_progress
import logging
from rest_framework import status
from django.utils import timezone
from notification.models import Notification
from orders.utils.aws_notifications import send_push_notification
from django.db.models import Count

from .dynamodb import get_progress, update_component, COMPONENTS

# Create your views here.

client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
logger = logging.getLogger(__name__)


class MyOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get my orders",
        operation_description=(
            "Retrieve all orders of the authenticated user. "
            "Each order includes full PC build details, total price, status, and timestamps."
        ),
        responses={
            200: OrderSerializer(many=True),
            401: openapi.Response(description="Unauthorized"),
        },
        tags=["Orders"],
    )

    def get(self, request):
        orders = Order.objects.filter(user=request.user).order_by("-created_at")
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

class CreateRazorpayOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        order_uuid = request.data.get("order_id")

        if not order_uuid:
            return Response({"error": "order_id required"}, status=400)

        try:
            order = Order.objects.get(order_id=order_uuid, user=request.user)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)

        if order.status != "PAYMENT_PENDING":
            return Response({"error": "Order already paid or invalid"}, status=400)

        amount = int(order.total_price * 100)

        razorpay_order = client.order.create({
            "amount": amount,
            "currency": "INR",
            "payment_capture": 1
        })

        # create payment record
        Payment.objects.create(
            order=order,
            amount=order.total_price,
            currency="INR",
            status="CREATED",
            razorpay_order_id=razorpay_order["id"]
        )

        return Response({
            "razorpay_order_id": razorpay_order["id"],
            "amount": amount,
            "key": settings.RAZORPAY_KEY_ID
        }, status=200)
    
class CancelOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        try:
            order = Order.objects.get(order_id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)

        if order.status != "PAYMENT_PENDING":
            return Response(
                {"error": "Only unpaid orders can be cancelled"},
                status=400
            )

        order.status = "CANCELLED"
        order.save(update_fields=["status"])

        return Response({"status": "Order cancelled"}, status=200)
    
class VerifyRazorpayPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        razorpay_order_id = request.data.get("razorpay_order_id")
        razorpay_payment_id = request.data.get("razorpay_payment_id")
        razorpay_signature = request.data.get("razorpay_signature")

        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
            return Response({"error": "Missing payment fields"}, status=400)

        try:
            payment = Payment.objects.select_related("order").get(
                razorpay_order_id=razorpay_order_id
            )
        except Payment.DoesNotExist:
            return Response({"error": "Payment record not found"}, status=404)

        if payment.status == "SUCCESS":
            return Response({"status": "Already paid"}, status=200)

        # 🔐 Verify signature
        body = f"{razorpay_order_id}|{razorpay_payment_id}"

        expected_signature = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode(),
            body.encode(),
            hashlib.sha256
        ).hexdigest()

        if expected_signature != razorpay_signature:
            payment.status = "FAILED"
            payment.save(update_fields=["status"])
            return Response({"status": "Payment verification failed"}, status=400)

        # ✅ ATOMIC TRANSACTION
        with transaction.atomic():
            payment = Payment.objects.select_for_update().get(id=payment.id)

            if payment.status == "SUCCESS":
                return Response({"status": "Already paid"}, status=200)

            # ✅ Update payment
            payment.status = "SUCCESS"
            payment.razorpay_payment_id = razorpay_payment_id
            payment.razorpay_signature = razorpay_signature
            payment.paid_at = now()
            payment.save(update_fields=[
                "status",
                "razorpay_payment_id",
                "razorpay_signature",
                "paid_at"
            ])

            order = payment.order

            if order.status == "PAYMENT_PENDING":
                order.status = "CONFIRMED"

                # 🧾 Generate invoice
                invoice_file = generate_invoice(order)
                order.invoice_pdf = invoice_file

                order.save(update_fields=["status", "invoice_pdf"])

                
        try:
            create_order_progress(order.order_id)
        except Exception as e:
            logger.error(f"DynamoDB creation failed: {e}")

        return Response({
            "status": "Payment successful",
            "order_status": payment.order.status
        }, status=200)
    
class WorkerOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        status = request.query_params.get("status")

        base_orders = Order.objects.filter(worker=request.user)

        # -------- ORIGINAL COUNTS FROM DB --------
        counts_queryset = (
            base_orders
            .values("status")
            .annotate(total=Count("id"))
        )

        counts = {row["status"]: row["total"] for row in counts_queryset}
        counts["TOTAL"] = base_orders.count()

        # -------- FILTER --------
        status_map = {
            "pending": "PAYMENT_PENDING",
            "in_progress": "BUILD_IN_PROGRESS",
            "completed": "COMPLETED",
        }

        orders = base_orders

        if status and status != "all":
            db_status = status_map.get(status)
            if db_status:
                orders = orders.filter(status=db_status)

        orders = orders.order_by("-created_at")

        serializer = OrderSerializer(orders, many=True)

        return Response({
            "orders": serializer.data,
            "counts": counts
        })
    
class WorkerOrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        order = get_object_or_404(
            Order,
            order_id=order_id,
            worker=request.user  # 🔒 ensures worker can only see their orders
        )

        serializer = OrderSerializer(order)
        return Response(serializer.data)
    

class VerifyComponentAPIView(APIView):

    def patch(self, request, order_id):

        component_name = request.data.get("component")

        if not component_name:
            return Response(
                {"error": "Component is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if component_name not in COMPONENTS:
            return Response(
                {"error": "Invalid component"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            updated_item = update_component(order_id, component_name)

            return Response(
                {
                    "message": "Component verified successfully",
                    "data": updated_item
                },
                status=status.HTTP_200_OK
            )

        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class WorkerProgressAPIView(APIView):

    def get(self, request, order_id):
       
        try:
            item = get_progress(order_id)

            if not item:
                create_order_progress(order_id)
                item = get_progress(order_id)

            return Response(item, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UpdateOrderStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    ALLOWED_TRANSITIONS = {
        "CONFIRMED": ["BUILD_IN_PROGRESS"],
        "BUILD_IN_PROGRESS": ["COMPLETED"],
    }

    def post(self, request, order_id):
        order = get_object_or_404(Order, order_id=order_id)
        new_status = request.data.get("status")

        # 🔐 Only worker allowed
        if request.user.role != "worker":
            return Response(
                {"error": "Only workers can update status."},
                status=status.HTTP_403_FORBIDDEN
            )

        # ❌ Invalid status
        if new_status not in dict(Order.STATUS_CHOICES):
            return Response(
                {"error": "Invalid status value."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 🔁 Validate transition
        allowed = self.ALLOWED_TRANSITIONS.get(order.status, [])
        if new_status not in allowed:
            return Response(
                {"error": f"Cannot change from {order.status} to {new_status}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = new_status
        order.save()
         # 🔔 Create notification
        if new_status == "BUILD_IN_PROGRESS":
            title = "Build Started"
            message = "Your PC build process has started."

        elif new_status == "COMPLETED":
            title = "Build Completed"
            message = "Your PC build has been completed successfully."

        else:
            title = None

        if title:
            Notification.objects.create(
                user=order.user,
                title=title,
                message=message
            )

            # 🚀 Trigger AWS Lambda
            try:
                send_push_notification(
                        order.user.email,
                        title,
                        message,
                        order.order_id
                    )
            except Exception as e:
                print("Lambda error:", e)

        return Response(
            {
                "message": "Status updated successfully.",
                "order_id": order.order_id,
                "new_status": order.status,
            },
            status=status.HTTP_200_OK
        )
    
class CreateWorkerReviewAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = WorkerReviewSerializer(
            data=request.data,
            context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Review submitted successfully"},
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
