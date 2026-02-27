from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import Order
from .serializers import OrderSerializer
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Create your views here.
class MyOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get my orders",
        operation_description=(
            "Retrieve all orders of the authenticated user. "
            "Each order includes full PC build details, total price, status, and timestamps."
        ),
        responses={
            200: OrderSerializer(many=True),
            401: openapi.Response(description="Unauthorized"),
        },
        tags=["Orders"],
    )

    def get(self, request):
        orders = Order.objects.filter(user=request.user).order_by("-created_at")
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)