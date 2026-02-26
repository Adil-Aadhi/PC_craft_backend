from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from products.models import Product
from .serializers import (
    CPUSerializer,
    MotherboardSerializer,
    RAMSerializer,
    GPUSerializer,
    PSUSerializer,
    StorageSerializer,
    CabinetSerializer,
    CaseFanSerializer,
    CoolerSerializer
)
from .utils.pagination import ComponentPagination

# Create your views here.

class BaseComponentListView(ListAPIView):
    serializer_class = None
    category_name = None
    spec_related = None
    pagination_class = ComponentPagination

    def get_queryset(self):
        queryset = Product.objects.filter(
            category__name=self.category_name,
            is_active=True,
            is_deleted=False,
        ).select_related(
            self.spec_related, "brand", "category"
        ).order_by("-id")

        # 🔎 SEARCH
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(name__icontains=search)

        # 💰 PRICE FILTER
        price = self.request.query_params.get("price")

        if price == "lt20":  # < 20000
            queryset = queryset.filter(price__lt=20000)

        elif price == "20to50":  # 20000 - 50000
            queryset = queryset.filter(price__gte=20000, price__lte=50000)

        elif price == "gt50":  # > 50000
            queryset = queryset.filter(price__gt=50000)

        return queryset
    
class CPUListView(BaseComponentListView):
    serializer_class = CPUSerializer
    category_name = "CPU"
    spec_related = "cpu_spec"

class MotherboardListView(BaseComponentListView):
    serializer_class = MotherboardSerializer
    category_name = "Motherboard"
    spec_related = "motherboard_spec"

class RAMListView(BaseComponentListView):
    serializer_class = RAMSerializer
    category_name = "RAM"
    spec_related = "ram_spec"

class GPUListView(BaseComponentListView):
    serializer_class = GPUSerializer
    category_name = "GPU"
    spec_related = "gpu_spec"

class PSUListView(BaseComponentListView):
    serializer_class = PSUSerializer
    category_name = "PSU"
    spec_related = "psu_spec"

class StorageListView(BaseComponentListView):
    serializer_class = StorageSerializer
    category_name = "Storage"
    spec_related = "storage_spec"

class CaseListView(BaseComponentListView):
    serializer_class = CabinetSerializer
    category_name = "Case"
    spec_related = "case_spec"

class CaseFanListView(BaseComponentListView):
    serializer_class = CaseFanSerializer
    category_name = "Case Fan"
    spec_related = "casefan_spec"

class CoolerListView(BaseComponentListView):
    serializer_class = CoolerSerializer
    category_name = "Cooler"
    spec_related = "cooler_spec"