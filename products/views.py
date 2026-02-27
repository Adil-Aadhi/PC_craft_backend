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
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Create your views here.

class BaseComponentListView(ListAPIView):
    serializer_class = None
    category_name = None
    spec_related = None
    pagination_class = ComponentPagination

    @swagger_auto_schema(
        operation_summary="List components",
        operation_description=(
            "Retrieve paginated list of components with optional search "
            "and price filters."
        ),
        manual_parameters=[
            openapi.Parameter(
                "search",
                openapi.IN_QUERY,
                description="Search by product name",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "price",
                openapi.IN_QUERY,
                description="Price filter: lt20 | 20to50 | gt50",
                type=openapi.TYPE_STRING,
                enum=["lt20", "20to50", "gt50"],
            ),
            openapi.Parameter(
                "page",
                openapi.IN_QUERY,
                description="Page number",
                type=openapi.TYPE_INTEGER,
            ),
        ],
        responses={200: openapi.Response(description="Component list")},
        tags=["Components"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Product.objects.filter(
            category__name=self.category_name,
            is_active=True,
            is_deleted=False,
        ).select_related(
            self.spec_related, "brand", "category"
        ).order_by("-id")

       
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(name__icontains=search)

        
        price = self.request.query_params.get("price")

        if price == "lt20":  
            queryset = queryset.filter(price__lt=20000)

        elif price == "20to50":  
            queryset = queryset.filter(price__gte=20000, price__lte=50000)

        elif price == "gt50":  
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