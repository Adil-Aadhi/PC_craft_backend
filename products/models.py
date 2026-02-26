from django.db import models
from django.utils.text import slugify

# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    logo = models.ImageField(upload_to="brands/", blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Product(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    model_number = models.CharField(max_length=255, blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE,related_name="products")
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE,related_name="products")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.brand})"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(f"{self.name}-{self.model_number or ''}")
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def is_in_stock(self):
        return self.stock_quantity > 0

    class Meta:
        indexes = [
            models.Index(fields=["category", "is_active"]),
            models.Index(fields=["brand"]),
            models.Index(fields=["is_active", "is_deleted"])
        ]

class CPUSpec(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="cpu_spec")
    socket = models.CharField(max_length=50)
    cores = models.PositiveIntegerField()
    threads = models.PositiveIntegerField()
    base_clock = models.DecimalField(max_digits=5, decimal_places=2)
    boost_clock = models.DecimalField(max_digits=5, decimal_places=2)
    tdp = models.PositiveIntegerField(help_text="TDP in watts")
    has_integrated_graphics = models.BooleanField(default=False)
    series = models.CharField(max_length=50, blank=True, null=True)
    l3_cache = models.CharField(max_length=50, blank=True, null=True)
    description=models.TextField(blank=True, null=True)

    def __str__(self):
        return f"CPU Spec for {self.product.name}"

class RAMSpec(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="ram_spec")
    ram_type = models.CharField(max_length=20)
    capacity_gb = models.PositiveIntegerField()
    frequency_mhz = models.PositiveIntegerField()
    stick_count = models.PositiveIntegerField(default=1)
    voltage = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True)
    description=models.TextField(blank=True, null=True)

    def __str__(self):
        return f"RAM Spec for {self.product.name}"

class GPUSpec(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="gpu_spec")
    memory_gb = models.PositiveIntegerField()
    memory_type = models.CharField(max_length=20)
    base_clock_mhz = models.PositiveIntegerField()
    boost_clock_mhz = models.PositiveIntegerField(blank=True, null=True)
    length_mm = models.PositiveIntegerField(help_text="GPU length in mm")
    tdp = models.PositiveIntegerField(help_text="TDP in watts")
    recommended_psu_watt = models.PositiveIntegerField(blank=True, null=True)
    gpu_chipset = models.CharField(max_length=100)
    description=models.TextField(blank=True, null=True)

    def __str__(self):
        return f"GPU Spec for {self.product.name}"

class MotherboardSpec(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="motherboard_spec")
    socket = models.CharField(max_length=50)
    chipset = models.CharField(max_length=50)
    ram_type = models.CharField(max_length=20)
    max_ram_gb = models.PositiveIntegerField()
    ram_slots = models.PositiveIntegerField()
    form_factor = models.CharField(max_length=20)
    pcie_version = models.CharField(max_length=10, blank=True, null=True)
    m2_slots = models.PositiveIntegerField(blank=True, null=True)
    sata_ports = models.PositiveIntegerField(blank=True, null=True)
    description=models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Motherboard Spec for {self.product.name}"

class CASESpec(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="case_spec")
    supported_form_factors = models.CharField(max_length=100)
    max_gpu_length_mm = models.PositiveIntegerField()
    max_cpu_cooler_height_mm = models.PositiveIntegerField(blank=True, null=True)
    has_rgb = models.BooleanField(default=False)
    side_panel = models.CharField(max_length=100)
    supported_fan_sizes = models.CharField(max_length=100, blank=True, null=True)
    description=models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Case Spec for {self.product.name}"

class STORAGESpec(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="storage_spec")
    storage_type = models.CharField(max_length=20)  # SSD / HDD / NVMe
    interface = models.CharField(max_length=20)     # SATA / NVMe / PCIe Gen4
    capacity_gb = models.PositiveIntegerField()
    read_speed = models.PositiveIntegerField(help_text="MB/s")
    write_speed = models.PositiveIntegerField(help_text="MB/s")
    form_factor = models.CharField(max_length=20, blank=True, null=True)  # 2.5, 3.5, M.2
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Storage Spec for {self.product.name}"

class PSUSpec(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="psu_spec")
    wattage = models.PositiveIntegerField(help_text="Wattage in watts")
    modular_type = models.CharField(max_length=100)
    efficiency_rating = models.CharField(max_length=20)
    form_factor = models.CharField(max_length=20, blank=True, null=True)
    description=models.TextField(blank=True, null=True)

    def __str__(self):
        return f"PSU Spec for {self.product.name}"

class CASEFANSpec(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="casefan_spec")
    fan_size = models.CharField(max_length=20)
    rpm = models.PositiveIntegerField()
    has_rgb = models.BooleanField(default=False)
    description=models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Case Fan Spec for {self.product.name}"

class COOLERSpec(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="cooler_spec")
    cooler_type = models.CharField(max_length=50)  # Air / Liquid
    supported_sockets = models.CharField(max_length=100)
    # Example: "AM4,AM5,LGA1700"
    cooler_height_mm = models.PositiveIntegerField(blank=True, null=True)
    fan_size = models.CharField(max_length=20, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    def __str__(self):
        return f"Cooler Spec for {self.product.name}"