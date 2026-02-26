from django.db import models
from Authentication.models import User
from products.models import Product

# Create your models here.
class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class CartItem(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("submitted", "Submitted"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
    ]

    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")

    build_name = models.CharField(max_length=100, blank=True, null=True)

    cpu = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name="+")
    motherboard = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name="+")
    ram = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name="+")
    gpu = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name="+")
    psu = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name="+")
    cooler = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name="+")
    storage = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name="+")
    case = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name="+")
    case_fan = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name="+")

    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_compatible = models.BooleanField(default=True)
    compatibility_notes = models.TextField(blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft"
    )

    assigned_worker = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_builds"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.build_name or 'PC Build'} - {self.cart.user}"