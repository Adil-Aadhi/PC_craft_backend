from django.db import models
from Authentication.models import User
import uuid

# Create your models here.
class Order(models.Model):

    STATUS_CHOICES = [
        ("PAYMENT_PENDING", "Payment Pending"),
        ("CONFIRMED", "Confirmed"),  # payment success
        ("BUILD_IN_PROGRESS", "Build In Progress"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    ]
    order_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True 
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")

    cart_item = models.OneToOneField(
        "cart.CartItem",
        on_delete=models.CASCADE,
        related_name="order"
    )

    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="INR")

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="PAYMENT_PENDING"
    )

    # optional: worker who accepted
    worker = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_orders"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} - {self.user}"
    

    
# class Payment(models.Model):

#     STATUS_CHOICES = [
#         ("CREATED", "Created"),
#         ("SUCCESS", "Success"),
#         ("FAILED", "Failed"),
#     ]

#     METHOD_CHOICES = [
#         ("RAZORPAY", "Razorpay"),
#         ("STRIPE", "Stripe"),
#     ]

#     order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments")

#     method = models.CharField(max_length=20, choices=METHOD_CHOICES)

#     amount = models.DecimalField(max_digits=10, decimal_places=2)
#     currency = models.CharField(max_length=10, default="INR")

#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="CREATED")

#     # 🔑 Gateway IDs
#     gateway_order_id = models.CharField(max_length=255, null=True, blank=True)
#     gateway_payment_id = models.CharField(max_length=255, null=True, blank=True)
#     gateway_signature = models.CharField(max_length=500, null=True, blank=True)

#     paid_at = models.DateTimeField(null=True, blank=True)

#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"Payment #{self.id} - Order #{self.order.id}"