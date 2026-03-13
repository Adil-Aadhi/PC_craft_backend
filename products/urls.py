from django.urls import path
from .views import (
    CPUListView, CPUDetailView,
    MotherboardListView, MotherboardDetailView,
    RAMListView, RAMDetailView,
    GPUListView, GPUDetailView,
    PSUListView, PSUDetailView,
    StorageListView, StorageDetailView,
    CaseListView, CaseDetailView,
    CaseFanListView, CaseFanDetailView,
    CoolerListView, CoolerDetailView
)

urlpatterns = [

    # CPU
    path("pc/cpu/", CPUListView.as_view(), name="pc-cpu"),
    path("pc/cpu/<int:pk>/", CPUDetailView.as_view(), name="pc-cpu-detail"),

    # Motherboard
    path("pc/motherboard/", MotherboardListView.as_view(), name="pc-motherboard"),
    path("pc/motherboard/<int:pk>/", MotherboardDetailView.as_view(), name="pc-motherboard-detail"),

    # RAM
    path("pc/ram/", RAMListView.as_view(), name="pc-ram"),
    path("pc/ram/<int:pk>/", RAMDetailView.as_view(), name="pc-ram-detail"),

    # GPU
    path("pc/gpu/", GPUListView.as_view(), name="pc-gpu"),
    path("pc/gpu/<int:pk>/", GPUDetailView.as_view(), name="pc-gpu-detail"),

    # PSU
    path("pc/psu/", PSUListView.as_view(), name="pc-psu"),
    path("pc/psu/<int:pk>/", PSUDetailView.as_view(), name="pc-psu-detail"),

    # Storage
    path("pc/storage/", StorageListView.as_view(), name="pc-storage"),
    path("pc/storage/<int:pk>/", StorageDetailView.as_view(), name="pc-storage-detail"),

    # Case
    path("pc/case/", CaseListView.as_view(), name="pc-case"),
    path("pc/case/<int:pk>/", CaseDetailView.as_view(), name="pc-case-detail"),

    # Case Fan
    path("pc/caseFan/", CaseFanListView.as_view(), name="pc-casefan"),
    path("pc/caseFan/<int:pk>/", CaseFanDetailView.as_view(), name="pc-casefan-detail"),

    # Cooler
    path("pc/cooler/", CoolerListView.as_view(), name="pc-cooler"),
    path("pc/cooler/<int:pk>/", CoolerDetailView.as_view(), name="pc-cooler-detail"),
]