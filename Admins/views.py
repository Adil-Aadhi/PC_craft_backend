from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from Authentication.models import User,WorkerProfile
from .serializers import AdminUserDetailSerializer,PendingWorkerSerializer,CompletedOrderSerializer,AdminOrderSerializer,RevenueDashboardSerializer,AdminDashboardSerializer,AdminProductSerializer,ProductCreateSerializer,CategorySerializer,AdminProductUpdateSerializer,AdminProductDetailSerializer
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from rest_framework.generics import ListAPIView ,RetrieveUpdateAPIView
from rest_framework import status
from notification.models import Notification
from orders.models import Order
from .models import WorkerEarning,AdminRevenue
from django.db import transaction
from .pagination import AdminOrderPagination,AdminProductPagination
from django.db.models import Sum, Avg, Count
from django.db.models.functions import TruncMonth
from products.models import Product,Category
from rest_framework.parsers import MultiPartParser, FormParser ,JSONParser

 

# Create your views here.
class AdminUsersView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        search = request.GET.get("search", "")
        role = request.GET.get("role", "all")
        status = request.GET.get("status", "all")
        page = int(request.GET.get("page", 1))
        limit = int(request.GET.get("limit", 10))

        users = User.objects.exclude(role="admin").select_related(
            "worker_profile", "user_profile"
        )

        # 🔍 Search
        if search:
            users = users.filter(
                Q(username__icontains=search)
                | Q(email__icontains=search)
                | Q(id__icontains=search)
            )

        # 🎭 Role filter
        if role != "all":
            users = users.filter(role=role)

        # 🚦 Status filter
        if status == "active":
            users = users.filter(is_active=True)
        elif status == "blocked":
            users = users.filter(is_active=False)

        # 📄 Pagination
        paginator = Paginator(users, limit)
        page_obj = paginator.get_page(page)

        serializer = AdminUserDetailSerializer(page_obj.object_list, many=True)

        return Response({
            "results": serializer.data,
            "total": paginator.count,
            "total_pages": paginator.num_pages,
            "current_page": page
        })
    
class ToggleUserStatus(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, user_id):
        user = get_object_or_404(User, id=user_id)

        user.is_active = not user.is_active
        user.save()

        return Response({
            "message": "User status updated",
            "is_active": user.is_active
        })
    
class AdminUserStatsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        users = User.objects.exclude(role="admin")

        total_users = users.count()
        active_users = users.filter(is_active=True).count()
        blocked_users = users.filter(is_active=False).count()

        pending_kyc = WorkerProfile.objects.filter(
            kyc_status="pending"
        ).count()

        return Response({
            "total_users": total_users,
            "active_users": active_users,
            "blocked_users": blocked_users,
            "pending_kyc": pending_kyc
        })
    
class PendingWorkersAPIView(ListAPIView):
    permission_classes = [IsAdminUser]

    serializer_class = PendingWorkerSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return WorkerProfile.objects.filter(kyc_status="pending").select_related("user")
    
class UpdateWorkerKYCAPIView(APIView):

    permission_classes = [IsAdminUser]

    def patch(self, request, pk):

        try:
            worker = WorkerProfile.objects.get(pk=pk)
        except WorkerProfile.DoesNotExist:
            return Response(
                {"error": "Worker not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        kyc_status = request.data.get("kyc_status")

        if kyc_status not in ["approved", "rejected"]:
            return Response(
                {"error": "Invalid status"},
                status=status.HTTP_400_BAD_REQUEST
            )

        worker.kyc_status = kyc_status
        worker.save()
         # 🔔 Create Notification
        if kyc_status == "approved":
            Notification.objects.create(
                user=worker.user,
                title="KYC Approved ✅",
                message="Congratulations! Your identity verification has been approved. You can now start receiving service requests."
            )
        elif kyc_status == "rejected":
            Notification.objects.create(
                user=worker.user,
                title="KYC Rejected ❌",
                message="Your identity verification was rejected. Please review your documents and resubmit your KYC."
            )

        return Response(
            {
                "message": f"Worker KYC {kyc_status} successfully"
            },
            status=status.HTTP_200_OK
        )
    
class CompletedOrdersAPIView(APIView):

    permission_classes = [IsAdminUser]

    def get(self, request):

        orders = (
            Order.objects
            .filter(status="COMPLETED")
            .select_related("worker", "user")
            .order_by("-created_at")
        )

        serializer = CompletedOrderSerializer(orders, many=True)

        return Response(serializer.data)
    
class ApprovePaymentAPIView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, order_id):

        order = get_object_or_404(
            Order.objects.select_related("worker"),
            order_id=order_id
        )

        # Prevent duplicate payout
        if WorkerEarning.objects.filter(order=order).exists():
            return Response(
                {"message": "Payment already approved"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if order.status != "COMPLETED":
            return Response(
                {"message": "Order not completed yet"},
                status=status.HTTP_400_BAD_REQUEST
            )

        worker = order.worker

        if not worker:
            return Response(
                {"message": "No worker assigned"},
                status=status.HTTP_400_BAD_REQUEST
            )

        component_cost = order.components_total
        service_fee = order.worker_earning
        platform_fee = order.platform_fee

        with transaction.atomic():

            # Create Worker Earning
            worker_earning = WorkerEarning.objects.create(
                worker=worker,
                order=order,
                component_reimbursement=component_cost,
                service_earning=service_fee,
            )

            # Create Admin Revenue
            admin_revenue = AdminRevenue.objects.create(
                order=order,
                platform_fee=platform_fee
            )

        return Response({
            "message": "Payment approved successfully",
            "worker_payout": worker_earning.payout_amount,
            "platform_fee": admin_revenue.platform_fee
        })
    
class AdminOrderListAPIView(ListAPIView):

    serializer_class = AdminOrderSerializer
    permission_classes = [IsAdminUser]
    pagination_class = AdminOrderPagination

    def get_queryset(self):

        queryset = Order.objects.select_related(
            "user",
            "worker",
            "cart_item"
        ).order_by("-created_at")

        # search
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(user__username__icontains=search) |
                Q(user__email__icontains=search) |
                Q(order_id__icontains=search)
            )

        # status filter
        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status__iexact=status)

        return queryset
    
    
class AdminRevenueDashboardAPIView(APIView):

    permission_classes = [IsAdminUser]

    def get(self, request):

        total_revenue = Order.objects.aggregate(
            total=Sum("total_price")
        )["total"] or 0

        worker_payout = WorkerEarning.objects.aggregate(
            total=Sum("payout_amount")
        )["total"] or 0

        platform_profit = AdminRevenue.objects.aggregate(
            total=Sum("platform_fee")
        )["total"] or 0

        total_orders = Order.objects.count()

        completed_orders = Order.objects.filter(
            status="COMPLETED"
        ).count()

        avg_order_value = Order.objects.aggregate(
            avg=Avg("total_price")
        )["avg"] or 0

        monthly_revenue = (
            Order.objects
            .annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(total=Sum("total_price"))
            .order_by("month")
        )

        monthly_data = [
            {
                "month": item["month"].strftime("%b"),
                "revenue": item["total"]
            }
            for item in monthly_revenue
        ]

        top_workers = (
            WorkerEarning.objects
            .values("worker__username")
            .annotate(total=Sum("payout_amount"))
            .order_by("-total")[:5]
        )

        workers_data = [
            {
                "worker": w["worker__username"],
                "earning": w["total"]
            }
            for w in top_workers
        ]

        data = {
            "total_revenue": total_revenue,
            "worker_payout": worker_payout,
            "platform_profit": platform_profit,
            "total_orders": total_orders,
            "completed_orders": completed_orders,
            "avg_order_value": avg_order_value,
            "monthly_revenue": monthly_data,
            "top_workers": workers_data,
        }

        serializer = RevenueDashboardSerializer(data)

        return Response(serializer.data) 
    
class AdminDashboardAPIView(APIView):

    permission_classes = [IsAdminUser]

    def get(self, request):

        # total users
        total_users = User.objects.filter(role="user").count()

        # total workers
        total_workers = User.objects.filter(role="worker").count()

        # total orders
        total_orders = Order.objects.count()

        # total revenue
        total_revenue = AdminRevenue.objects.aggregate(
            total=Sum("platform_fee")
        )["total"] or 0

        # revenue growth per month
        revenue_qs = (
            AdminRevenue.objects
            .annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(revenue=Sum("platform_fee"))
            .order_by("month")
        )

        revenue_growth = [
            {
                "month": item["month"].strftime("%b"),
                "revenue": item["revenue"]
            }
            for item in revenue_qs
        ]

        data = {
            "total_users": total_users,
            "total_workers": total_workers,
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "revenue_growth": revenue_growth
        }

        serializer = AdminDashboardSerializer(data)

        return Response(serializer.data)
    
class AdminProductsAPIView(APIView):

    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):

        queryset = Product.objects.filter(is_deleted=False, is_active=True)

        search = request.GET.get("search")
        category = request.GET.get("category")
        brand = request.GET.get("brand")
        min_price = request.GET.get("min_price")
        max_price = request.GET.get("max_price")

        # Search
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(model_number__icontains=search)
            )

        # Category filter
        if category:
            queryset = queryset.filter(category__slug=category)

        # Brand filter
        if brand:
            queryset = queryset.filter(brand__slug=brand)

        # Price filter
        if min_price:
            queryset = queryset.filter(price__gte=min_price)

        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        queryset = queryset.select_related("category", "brand").order_by("-created_at")

        # Pagination
        paginator = AdminProductPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)

        serializer = AdminProductSerializer(paginated_queryset, many=True)

        return paginator.get_paginated_response(serializer.data)
    
    def post(self, request):

        serializer = ProductCreateSerializer(data=request.data)

        if serializer.is_valid():
            product = serializer.save()

            return Response(
                {"message": "Product created successfully", "id": product.id},
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CategoryListAPIView(APIView):

    permission_classes = [IsAdminUser]

    def get(self, request):
        categories = Category.objects.filter(is_active=True)

        serializer = CategorySerializer(categories, many=True)

        return Response(serializer.data)


class AdminProductDetailView(RetrieveUpdateAPIView):

    permission_classes = [IsAdminUser]

    parser_classes = [MultiPartParser, FormParser , JSONParser]

    queryset = Product.objects.select_related(
        "category",
        "brand"
    ).prefetch_related(
        "cpu_spec",
        "gpu_spec",
        "ram_spec",
        "motherboard_spec",
        "storage_spec",
        "psu_spec",
        "case_spec",
        "casefan_spec",
        "cooler_spec"
    )

    def get_serializer_class(self):

        if self.request.method in ["PUT", "PATCH"]:
            return AdminProductUpdateSerializer

        return AdminProductDetailSerializer
    
class AdminProductDeleteAPIView(APIView):

    permission_classes = [IsAdminUser]

    def delete(self, request, pk):

        product = get_object_or_404(Product, pk=pk)

        product.is_deleted = True
        product.save(update_fields=["is_deleted"])

        return Response(
            {"message": "Product deleted successfully"},
            status=status.HTTP_200_OK
        )
    