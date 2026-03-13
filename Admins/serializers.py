from rest_framework import serializers
from Authentication.models import User,WorkerProfile
from users.models import Address
from Worker.models import WorkerIdentityKYC
from orders.models import Order
from cart.serializer import CartItemReadSerializer
from .models import WorkerEarning,AdminRevenue
from products.models import Brand,Category,Product,CPUSpec, RAMSpec, GPUSpec, MotherboardSpec,CASESpec, STORAGESpec, PSUSpec, CASEFANSpec, COOLERSpec
from django.db import transaction
import json
from django.db import models
from products.serializers import CPUSerializer,GPUSerializer,RAMSerializer,StorageSerializer,PSUSerializer,CabinetSerializer,CaseFanSerializer,CoolerSerializer,MotherboardSerializer



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

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug"]

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ["id", "name", "slug"]
class AdminProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    in_stock = serializers.BooleanField(source="is_in_stock", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "model_number",
            "category",
            "brand",
            "price",
            "stock_quantity",
            "in_stock",
            "image",
            "created_at"
        ]

SPEC_MODEL_MAP = {
    "cpu": CPUSpec,
    "gpu": GPUSpec,
    "ram": RAMSpec,
    "motherboard": MotherboardSpec,
    "case": CASESpec,
    "storage": STORAGESpec,
    "psu": PSUSpec,
    "case-fan": CASEFANSpec,
    "cooler": COOLERSpec,
}

class ProductCreateSerializer(serializers.ModelSerializer):

    spec = serializers.JSONField(write_only=True)

    class Meta:
        model = Product
        fields = [
            "name",
            "model_number",
            "category",
            "brand",
            "price",
            "stock_quantity",
            "image",
            "spec"
        ]

    def create(self, validated_data):

        spec_data = validated_data.pop("spec")

        if isinstance(spec_data, str):
            spec_data = json.loads(spec_data)

        category = validated_data["category"]
        category_slug = category.slug

        with transaction.atomic():

            product = Product.objects.create(**validated_data)

            spec_model = SPEC_MODEL_MAP.get(category_slug)

            if spec_model:

                valid_fields = {
                    field.name
                    for field in spec_model._meta.fields
                }

                filtered_spec = {
                    key: value
                    for key, value in spec_data.items()
                    if key in valid_fields and value not in ["", None]
                }

                # 🔹 Convert values to correct types
                for field in spec_model._meta.fields:

                    name = field.name

                    if name in filtered_spec:

                        value = filtered_spec[name]

                        # Boolean conversion
                        if isinstance(field, models.BooleanField) and isinstance(value, str):
                            filtered_spec[name] = value.lower() == "true"

                        # Integer conversion
                        if isinstance(field, models.IntegerField) and isinstance(value, str):
                            filtered_spec[name] = int(value)

                        # Float / Decimal conversion
                        if isinstance(field, (models.FloatField, models.DecimalField)) and isinstance(value, str):
                            filtered_spec[name] = float(value)

                spec_model.objects.create(product=product, **filtered_spec)

        return product
    
class AdminProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    brand = BrandSerializer(read_only=True)

    spec = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "model_number",
            "category",
            "brand",
            "price",
            "stock_quantity",
            "image",
            "created_at",
            "spec"
        ]

    def get_spec(self, obj):

        if hasattr(obj, "cpu_spec"):
            return CPUSerializer(obj).data

        if hasattr(obj, "gpu_spec"):
            return GPUSerializer(obj).data

        if hasattr(obj, "ram_spec"):
            return RAMSerializer(obj).data

        if hasattr(obj, "motherboard_spec"):
            return MotherboardSerializer(obj).data

        if hasattr(obj, "storage_spec"):
            return StorageSerializer(obj).data

        if hasattr(obj, "psu_spec"):
            return PSUSerializer(obj).data

        if hasattr(obj, "case_spec"):
            return CabinetSerializer(obj).data

        if hasattr(obj, "casefan_spec"):
            return CaseFanSerializer(obj).data

        if hasattr(obj, "cooler_spec"):
            return CoolerSerializer(obj).data

        return None
    
class AdminProductUpdateSerializer(serializers.ModelSerializer):

    image = serializers.FileField(required=False, write_only=True)
    spec = serializers.JSONField(required=False)

    class Meta:
        model = Product
        fields = [
            "name",
            "model_number",
            "price",
            "stock_quantity",
            "category",
            "brand",
            "image",
            "spec" 
        ]

    def update(self, instance, validated_data):
        request = self.context.get("request")
        spec_data = validated_data.pop("spec", None)
        
        # 1. Update the Product fields
        for attr, value in validated_data.items():
            if attr != "image": # Handled separately below
                setattr(instance, attr, value)

        if request.FILES.get("image"):
            instance.image = request.FILES["image"]

        instance.save()

        # 2. Handle Specifications
        if isinstance(spec_data, str):
            try:
                spec_data = json.loads(spec_data)
            except json.JSONDecodeError:
                spec_data = {}

        spec_model = SPEC_MODEL_MAP.get(instance.category.slug)

        if spec_model and spec_data:
            valid_fields = {field.name for field in spec_model._meta.fields}
            
            # Remove 'id' and 'product' from data to prevent manual overwrite errors
            filtered_spec = {
                key: value
                for key, value in spec_data.items()
                if key in valid_fields and key not in ["id", "product"] and value not in ["", None]
            }

            # This replaces the entire try/except block
            spec_model.objects.update_or_create(
                product=instance, 
                defaults=filtered_spec
            )

        return instance