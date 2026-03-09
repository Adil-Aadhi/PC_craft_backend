from rest_framework import serializers
from .models import CartItem,Cart
from products.serializers import CPUSerializer,MotherboardSerializer,RAMSerializer,GPUSerializer,PSUSerializer,CoolerSerializer,StorageSerializer,CaseFanSerializer,CabinetSerializer


class CartItemWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = [
            "build_name",
            "cpu",
            "motherboard",
            "ram",
            "gpu",
            "psu",
            "cooler",
            "storage",
            "case",
            "case_fan",
        ]
class CartItemReadSerializer(serializers.ModelSerializer):
    cpu = CPUSerializer(read_only=True)
    motherboard = MotherboardSerializer(read_only=True)
    ram = RAMSerializer(read_only=True)
    gpu = GPUSerializer(read_only=True)
    psu = PSUSerializer(read_only=True)
    cooler = CoolerSerializer(read_only=True)
    storage = StorageSerializer(read_only=True)
    case = CabinetSerializer(read_only=True)
    case_fan = CaseFanSerializer(read_only=True)

    class Meta:
        model = CartItem
        fields = [
            "id",
            "build_name",
            "cpu",
            "motherboard",
            "ram",
            "gpu",
            "psu",
            "cooler",
            "storage",
            "case",
            "case_fan",
            "total_price",
            "is_compatible",
            "compatibility_notes",
            "created_at",
            "status",
        ]

class CartSerializer(serializers.ModelSerializer):
    items = CartItemReadSerializer(many=True, read_only=True)
    total_builds = serializers.SerializerMethodField()
    cart_total_price = serializers.SerializerMethodField()
    total_components = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = [
            "id",
            "items",
            "total_builds",
            "cart_total_price",
            "total_components",
        ]

    def get_total_builds(self, obj):
        return obj.items.count()

    def get_cart_total_price(self, obj):
        return sum(item.total_price or 0 for item in obj.items.all())

    def get_total_components(self, obj):
        total = 0
        for item in obj.items.all():
            total += len([
                item.cpu,
                item.motherboard,
                item.ram,
                item.gpu,
                item.storage,
                item.cooler,
                item.case_fan,
                item.psu,
                item.case,
            ])
        return total