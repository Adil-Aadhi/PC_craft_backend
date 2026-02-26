from django.urls import path
from .views import CartView,updateCartItemView,CartItemSummaryView,ChatBuildDetailView,UpdateBuildStatusView

urlpatterns = [
    path('items/', CartView.as_view(), name='cart-item'),
    path('items/<int:item_id>/', updateCartItemView.as_view(), name='cart-delete'),
    path("items/<int:item_id>/summary/", CartItemSummaryView.as_view(), name='cart-summary'),
    path("items/<int:item_id>/chat/", ChatBuildDetailView.as_view(), name='cart-build-chat'),
    path("items/<int:item_id>/status/", UpdateBuildStatusView.as_view(), name='cart-status'),
]