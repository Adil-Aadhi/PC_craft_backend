from django.urls import path
from .views import CPUListView,MotherboardListView,RAMListView,GPUListView,PSUListView,StorageListView,CaseListView,CaseFanListView,CoolerListView

urlpatterns=[
    path("pc/cpu/", CPUListView.as_view(),name="pc-cpu"),
    path("pc/motherboard/", MotherboardListView.as_view(),name="pc-motherboard"),
    path("pc/ram/", RAMListView.as_view(),name="pc-ram"),
    path("pc/gpu/", GPUListView.as_view(),name="pc-gpu"),
    path("pc/psu/", PSUListView.as_view(),name="pc-psu"),
    path("pc/storage/", StorageListView.as_view(),name="pc-storage"),
    path("pc/case/", CaseListView.as_view(),name="pc-case"),
    path("pc/caseFan/", CaseFanListView.as_view(),name="pc-casefan"),
    path("pc/cooler/", CoolerListView.as_view(),name="pc-cooler"),
]