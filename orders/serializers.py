from rest_framework import serializers
from .models import Order
from cart.serializer import CartItemReadSerializer 
from Authentication.models import WorkerReview
from django.db.models import Avg

class WorkerReviewDisplaySerializer(serializers.ModelSerializer):

    class Meta:
        model = WorkerReview
        fields = ["rating", "review_text"]


class OrderSerializer(serializers.ModelSerializer):

    build = CartItemReadSerializer(source="cart_item", read_only=True)
    order_id = serializers.UUIDField(read_only=True)
    quotation_pdf = serializers.FileField(read_only=True)
    invoice_pdf = serializers.FileField(read_only=True)

    username = serializers.CharField(source="user.username", read_only=True)

    review = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "order_id",
            "build",          # 🔥 full build details here
            "total_price",
            "status",
            "quotation_pdf",
            "invoice_pdf",
            "created_at",
            "username",
            "review"
        ]
    def get_review(self, obj):
        review = WorkerReview.objects.filter(order=obj).first()
        if review:
            return WorkerReviewDisplaySerializer(review).data
        return None
    
class WorkerReviewSerializer(serializers.ModelSerializer):

    class Meta:
        model = WorkerReview
        fields = ["order", "rating", "review_text"]

    def validate(self, data):
        request = self.context["request"]
        user = request.user
        order = data["order"]

        # check order belongs to user
        if order.user != user:
            raise serializers.ValidationError("You cannot review this order.")

        # check order completed
        if order.status != "COMPLETED":
            raise serializers.ValidationError("You can review only completed orders.")

        # check review already exists
        if hasattr(order, "review"):
            raise serializers.ValidationError("Review already submitted.")

        return data

    def create(self, validated_data):
        user = self.context["request"].user
        order = validated_data["order"]
        worker = order.worker.worker_profile   # adjust if your relation is different

        review = WorkerReview.objects.create(
            user=user,
            worker=worker,
            order=order,
            rating=validated_data["rating"],
            review_text=validated_data.get("review_text")
        )

        # update worker rating
        avg = worker.reviews.aggregate(avg=Avg("rating"))["avg"] or 0
        worker.rating = round(avg, 2)
        worker.review_count = worker.reviews.count()
        worker.save()

        return review