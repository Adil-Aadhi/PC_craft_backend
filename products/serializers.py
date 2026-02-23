from rest_framework import serializers
from products.models import Product


# 🧠 COMMON PRODUCT FIELDS
class BaseProductSerializer(serializers.ModelSerializer):
    brand = serializers.StringRelatedField()
    category = serializers.StringRelatedField()

    class Meta:
        model = Product
        fields = ["id", "name", "price", "brand", "image"]

class CPUSerializer(BaseProductSerializer):
    socket = serializers.CharField(source="cpu_spec.socket")
    cores = serializers.IntegerField(source="cpu_spec.cores")
    threads = serializers.IntegerField(source="cpu_spec.threads")
    base_clock = serializers.DecimalField(source="cpu_spec.base_clock", max_digits=5, decimal_places=2)
    boost_clock = serializers.DecimalField(source="cpu_spec.boost_clock", max_digits=5, decimal_places=2)
    tdp = serializers.IntegerField(source="cpu_spec.tdp")

    class Meta(BaseProductSerializer.Meta):
        fields = BaseProductSerializer.Meta.fields + [
            "socket",
            "cores",
            "threads",
            "base_clock",
            "boost_clock",
            "tdp",
        ]

class RAMSerializer(BaseProductSerializer):
    ram_type = serializers.CharField(source="ram_spec.ram_type")
    capacity_gb = serializers.IntegerField(source="ram_spec.capacity_gb")
    frequency_mhz = serializers.IntegerField(source="ram_spec.frequency_mhz")
    stick_count = serializers.IntegerField(source="ram_spec.stick_count")

    class Meta(BaseProductSerializer.Meta):
        fields = BaseProductSerializer.Meta.fields + [
            "ram_type",
            "capacity_gb",
            "frequency_mhz",
            "stick_count",
        ]

class GPUSerializer(BaseProductSerializer):
    memory_gb = serializers.IntegerField(source="gpu_spec.memory_gb")
    memory_type = serializers.CharField(source="gpu_spec.memory_type")
    length_mm = serializers.IntegerField(source="gpu_spec.length_mm")
    tdp = serializers.IntegerField(source="gpu_spec.tdp")
    recommended_psu_watt = serializers.IntegerField(source="gpu_spec.recommended_psu_watt")

    class Meta(BaseProductSerializer.Meta):
        fields = BaseProductSerializer.Meta.fields + [
            "memory_gb",
            "memory_type",
            "length_mm",
            "tdp",
            "recommended_psu_watt",
        ]

class MotherboardSerializer(BaseProductSerializer):
    socket = serializers.CharField(source="motherboard_spec.socket")
    chipset = serializers.CharField(source="motherboard_spec.chipset")
    ram_type = serializers.CharField(source="motherboard_spec.ram_type")
    max_ram_gb = serializers.IntegerField(source="motherboard_spec.max_ram_gb")
    ram_slots = serializers.IntegerField(source="motherboard_spec.ram_slots")
    form_factor = serializers.CharField(source="motherboard_spec.form_factor")
    pcie_version = serializers.CharField(source="motherboard_spec.pcie_version")

    class Meta(BaseProductSerializer.Meta):
        fields = BaseProductSerializer.Meta.fields + [
            "socket",
            "chipset",
            "ram_type",
            "max_ram_gb",
            "ram_slots",
            "form_factor",
            "pcie_version",
        ]

class StorageSerializer(BaseProductSerializer):
    storage_type = serializers.CharField(source="storage_spec.storage_type")
    interface = serializers.CharField(source="storage_spec.interface")
    capacity_gb = serializers.IntegerField(source="storage_spec.capacity_gb")
    read_speed = serializers.IntegerField(source="storage_spec.read_speed")
    write_speed = serializers.IntegerField(source="storage_spec.write_speed")
    form_factor = serializers.CharField(source="storage_spec.form_factor")

    class Meta(BaseProductSerializer.Meta):
        fields = BaseProductSerializer.Meta.fields + [
            "storage_type",
            "interface",
            "capacity_gb",
            "read_speed",
            "write_speed",
            "form_factor",
        ]

class PSUSerializer(BaseProductSerializer):
    wattage = serializers.IntegerField(source="psu_spec.wattage")
    modular_type = serializers.CharField(source="psu_spec.modular_type")
    efficiency_rating = serializers.CharField(source="psu_spec.efficiency_rating")
    form_factor = serializers.CharField(source="psu_spec.form_factor")

    class Meta(BaseProductSerializer.Meta):
        fields = BaseProductSerializer.Meta.fields + [
            "wattage",
            "modular_type",
            "efficiency_rating",
            "form_factor",
        ]

class CabinetSerializer(BaseProductSerializer):
    supported_form_factors = serializers.CharField(source="case_spec.supported_form_factors")
    max_gpu_length_mm = serializers.IntegerField(source="case_spec.max_gpu_length_mm")
    max_cpu_cooler_height_mm = serializers.IntegerField(source="case_spec.max_cpu_cooler_height_mm")
    has_rgb = serializers.BooleanField(source="case_spec.has_rgb")
    side_panel = serializers.CharField(source="case_spec.side_panel")

    class Meta(BaseProductSerializer.Meta):
        fields = BaseProductSerializer.Meta.fields + [
            "supported_form_factors",
            "max_gpu_length_mm",
            "max_cpu_cooler_height_mm",
            "has_rgb",
            "side_panel",
        ]

class CaseFanSerializer(BaseProductSerializer):
    fan_size = serializers.CharField(source="casefan_spec.fan_size")
    rpm = serializers.IntegerField(source="casefan_spec.rpm")
    has_rgb = serializers.BooleanField(source="casefan_spec.has_rgb")
    description = serializers.CharField(
        source="casefan_spec.description", allow_null=True, allow_blank=True
    )

    class Meta(BaseProductSerializer.Meta):
        fields = BaseProductSerializer.Meta.fields + [
            "fan_size",
            "rpm",
            "has_rgb",
            "description",
        ]

class CoolerSerializer(BaseProductSerializer):
    cooler_type = serializers.CharField(source="cooler_spec.cooler_type")
    supported_sockets = serializers.CharField(source="cooler_spec.supported_sockets")
    cooler_height_mm = serializers.IntegerField(
        source="cooler_spec.cooler_height_mm", allow_null=True
    )
    fan_size = serializers.CharField(
        source="cooler_spec.fan_size", allow_null=True, allow_blank=True
    )
    description = serializers.CharField(
        source="cooler_spec.description", allow_null=True, allow_blank=True
    )

    class Meta(BaseProductSerializer.Meta):
        fields = BaseProductSerializer.Meta.fields + [
            "cooler_type",
            "supported_sockets",
            "cooler_height_mm",
            "fan_size",
            "description",
        ]