from django.db import models
from Authentication.models import User
from orders.models import Order

# Create your models here.
class WorkerEarning(models.Model):

    worker = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="worker_earnings"
    )
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name="worker_earning_record"
    )
    component_reimbursement = models.DecimalField(max_digits=10, decimal_places=2)
    service_earning = models.DecimalField(max_digits=10, decimal_places=2)
    payout_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.payout_amount = self.component_reimbursement + self.service_earning
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.worker} - Order {self.order.order_id}"

class AdminRevenue(models.Model):

    order = models.OneToOneField(
        Order,  
        on_delete=models.CASCADE,
        related_name="admin_revenue"
    )

    platform_fee = models.DecimalField(max_digits=10, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Revenue - {self.platform_fee}"