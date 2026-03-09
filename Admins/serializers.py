from rest_framework import serializers
from Authentication.models import User,WorkerProfile
from users.models import Address
from Worker.models import WorkerIdentityKYC
from orders.models import Order
from cart.serializer import CartItemReadSerializer
from .models import WorkerEarning,AdminRevenue



class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ["city", "state"]

class AdminUserDetailSerializer(serializers.ModelSerializer):
    kyc_status = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    profile_image = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    order_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "role",
            "is_active",
            "date_joined",
            "last_login",
            "kyc_status",
            "rating",
            "profile_image",
            "phone",
            "full_name",
            "address",
            "order_count",
        ]

    def get_kyc_status(self, obj):
        worker = getattr(obj, "worker_profile", None)
        return worker.kyc_status if worker else None

    def get_rating(self, obj):
        worker = getattr(obj, "worker_profile", None)
        return worker.rating if worker else None

    def get_profile_image(self, obj):
        profile = getattr(obj, "user_profile", None)
        worker = getattr(obj, "worker_profile", None)

        if profile and profile.profile_image:
            return profile.profile_image
        if worker and worker.profile_image:
            return worker.profile_image
        return None

    def get_phone(self, obj):
        profile = getattr(obj, "user_profile", None)
        return profile.phone if profile else None

    def get_full_name(self, obj):
        profile = getattr(obj, "user_profile", None)
        return profile.full_name if profile else None
    def get_address(self, obj):
        default_address = obj.addresses.filter(is_default=True).first()

        if default_address:
            return UserAddressSerializer(default_address).data

        return None
    def get_order_count(self, obj):
        return obj.orders.count()
    
class WorkerIdentityKYCSerializer(serializers.ModelSerializer):

    class Meta:
        model = WorkerIdentityKYC
        fields = [
            "id_type",
            "id_number",
            "id_front_url",
            "id_back_url",
            "created_at"
        ]

class PendingWorkerSerializer(serializers.ModelSerializer):

    worker_id = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    phone = serializers.CharField(source="user.user_profile.phone", read_only=True)
    date_of_birth = serializers.DateField(source="user.user_profile.date_of_birth", read_only=True)

    kyc_details = WorkerIdentityKYCSerializer(
        source="user.identity_kyc",
        read_only=True
    )

    class Meta:
        model = WorkerProfile
        fields = [
            "id",
            "worker_id",
            "username",
            "email",
            "gender",
            "skills",
            "experience_years",
            "hourly_rate",
            "kyc_status",
            "profile_image",
            "kyc_details",
            "phone",
            "date_of_birth"
        ]

class CompletedOrderSerializer(serializers.ModelSerializer):

    worker_name = serializers.CharField(source="worker.username", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)
    components = CartItemReadSerializer(source="cart_item", read_only=True)

    payout_approved = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "order_id",
            "worker_name",
            "user_email",
            "total_price", 
            "currency",
            "status",
            "created_at",
            "platform_fee",
            "worker_earning",
            "components",
            "payout_approved", 
        ]
    def get_payout_approved(self, obj):
        return hasattr(obj, "worker_earning_record")

class WorkerEarningSerializer(serializers.ModelSerializer):

    class Meta:
        model = WorkerEarning
        fields = "__all__"


class AdminRevenueSerializer(serializers.ModelSerializer):

    class Meta:
        model = AdminRevenue
        fields = "__all__"


class AdminOrderSerializer(serializers.ModelSerializer):

    user_username = serializers.CharField(source="user.username", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)

    worker_username = serializers.CharField(source="worker.username", read_only=True)

    cart_item = CartItemReadSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_id",
            "user_username",
            "user_email",
            "worker_username",
            "cart_item",
            "components_total",
            "platform_fee",
            "worker_earning",
            "total_price",
            "status",
            "created_at",
        ]


class RevenueDashboardSerializer(serializers.Serializer):

    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    worker_payout = serializers.DecimalField(max_digits=12, decimal_places=2)
    platform_profit = serializers.DecimalField(max_digits=12, decimal_places=2)

    total_orders = serializers.IntegerField()
    completed_orders = serializers.IntegerField()
    avg_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)

    monthly_revenue = serializers.ListField()
    top_workers = serializers.ListField()

class AdminDashboardSerializer(serializers.Serializer):

    total_users = serializers.IntegerField()
    total_workers = serializers.IntegerField()
    total_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)

    revenue_growth = serializers.ListField()