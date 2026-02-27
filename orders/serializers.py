from rest_framework import serializers
from .models import Order
from cart.serializer import CartItemReadSerializer 


class OrderSerializer(serializers.ModelSerializer):

    build = CartItemReadSerializer(source="cart_item", read_only=True)
    order_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_id",
            "build",          # 🔥 full build details here
            "total_price",
            "status",
            "created_at",
        ]