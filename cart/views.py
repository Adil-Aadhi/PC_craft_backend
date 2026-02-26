from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Prefetch
from .services import validate_build
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Cart, CartItem
from .serializer import CartItemWriteSerializer, CartItemReadSerializer, CartSerializer
from products.models import Product

# Create your views here.

class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart = (
            Cart.objects
            .filter(user=request.user)
            .prefetch_related(
                # Products
                "items__cpu",
                "items__motherboard",
                "items__ram",
                "items__gpu",
                "items__psu",
                "items__cooler",
                "items__storage",
                "items__case",
                "items__case_fan",

                # Brand & Category
                "items__cpu__brand", "items__cpu__category",
                "items__motherboard__brand", "items__motherboard__category",
                "items__ram__brand", "items__ram__category",
                "items__gpu__brand", "items__gpu__category",
                "items__psu__brand", "items__psu__category",
                "items__cooler__brand", "items__cooler__category",
                "items__storage__brand", "items__storage__category",
                "items__case__brand", "items__case__category",
                "items__case_fan__brand", "items__case_fan__category",

                # Spec tables
                "items__cpu__cpu_spec",
                "items__motherboard__motherboard_spec",
                "items__ram__ram_spec",
                "items__gpu__gpu_spec",
                "items__psu__psu_spec",
                "items__cooler__cooler_spec",
                "items__storage__storage_spec",
                "items__case__case_spec",
                "items__case_fan__casefan_spec",
            )
            .first()
        )

        if not cart:
            return Response({"items": []})

        serializer = CartSerializer(cart)
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    def post(self, request):
        write_serializer = CartItemWriteSerializer(data=request.data)
        write_serializer.is_valid(raise_exception=True)

        data = write_serializer.validated_data

        # 🔹 Get products with specs
        product_ids = [p.id for p in data.values() if isinstance(p, Product)]
        products = Product.objects.filter(id__in=product_ids).select_related(
            "cpu_spec",
            "motherboard_spec",
            "ram_spec",
            "gpu_spec",
            "psu_spec",
            "cooler_spec",
            "storage_spec",
            "case_spec",
            "casefan_spec",
        )
        product_map = {p.id: p for p in products}

        # 🔹 Run compatibility validation
        component_ids = {
                k: v.id if isinstance(v, Product) else None
                for k, v in data.items()
            }

        is_compatible, notes = validate_build(component_ids, product_map)

        # 🔹 Calculate total price
        total_price = sum(p.price for p in product_map.values() if p and p.price)

        # 🔹 Get or create cart
        cart, _ = Cart.objects.get_or_create(user=request.user)

        # 🔹 Save cart item
        cart_item = CartItem.objects.create(
            cart=cart,
            build_name=data.get("build_name"),
            cpu=data.get("cpu"),
            motherboard=data.get("motherboard"),
            ram=data.get("ram"),
            gpu=data.get("gpu"),
            psu=data.get("psu"),
            cooler=data.get("cooler"),
            storage=data.get("storage"),
            case=data.get("case"),
            case_fan=data.get("case_fan"),
            total_price=total_price,
            is_compatible=is_compatible,
            compatibility_notes=notes,
        )

        read_serializer = CartItemReadSerializer(cart_item)

        return Response(
            {
                "message": "Build added to cart",
                "item": read_serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )
    
class updateCartItemView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, item_id):
        cart_item = get_object_or_404(
            CartItem,
            id=item_id,
            cart__user=request.user
        )

        serializer = CartItemReadSerializer(cart_item)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, item_id):
        cart_item = get_object_or_404(
            CartItem,
            id=item_id,
            cart__user=request.user
        )

        serializer = CartItemWriteSerializer(
            cart_item,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        # 🔹 Update only provided fields
        for field, value in data.items():
            setattr(cart_item, field, value)

        # 🔹 Collect all components (existing + updated)
        components = {
            "cpu": cart_item.cpu,
            "motherboard": cart_item.motherboard,
            "ram": cart_item.ram,
            "gpu": cart_item.gpu,
            "psu": cart_item.psu,
            "cooler": cart_item.cooler,
            "storage": cart_item.storage,
            "case": cart_item.case,
            "case_fan": cart_item.case_fan,
        }

        # 🔹 Extract product IDs
        product_ids = [p.id for p in components.values() if isinstance(p, Product)]

        products = Product.objects.filter(id__in=product_ids).select_related(
            "cpu_spec",
            "motherboard_spec",
            "ram_spec",
            "gpu_spec",
            "psu_spec",
            "cooler_spec",
            "storage_spec",
            "case_spec",
            "casefan_spec",
        )

        product_map = {p.id: p for p in products}

        component_ids = {
            k: v.id if isinstance(v, Product) else None
            for k, v in components.items()
        }

        # 🔹 Re-run compatibility
        is_compatible, notes = validate_build(component_ids, product_map)

        # 🔹 Recalculate total price
        total_price = sum(p.price for p in product_map.values() if p and p.price)

        # 🔹 Save updated values
        cart_item.total_price = total_price
        cart_item.is_compatible = is_compatible
        cart_item.compatibility_notes = notes
        cart_item.save()

        return Response(
            {
                "message": "Build updated successfully",
                "item": CartItemReadSerializer(cart_item).data
            },
            status=status.HTTP_200_OK
        )
    

    def delete(self, request, item_id):
        cart_item = get_object_or_404(
            CartItem,
            id=item_id,
            cart__user=request.user  # 🔒 ensures ownership
        )

        cart_item.delete()

        return Response(
            {"message": "Build removed from cart"},
            status=status.HTTP_200_OK
        )

class CartItemSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, item_id):
        cart_item = get_object_or_404(CartItem, id=item_id)

        def get_name(product):
            if not product:
                return None
            return getattr(product, "product_name", None) or getattr(product, "name", None)

        return Response({
            "build_name": cart_item.build_name,
            "cpu": get_name(cart_item.cpu),
            "gpu": get_name(cart_item.gpu),
            "total_price": cart_item.total_price,
            "status": cart_item.status,
        })
    
class ChatBuildDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, item_id):
        cart_item = get_object_or_404(
            CartItem.objects.select_related(
                "cpu", "motherboard", "ram", "gpu", "psu",
                "cooler", "storage", "case", "case_fan"
            ).prefetch_related(
                # brand & category
                "cpu__brand", "cpu__category",
                "motherboard__brand", "motherboard__category",
                "ram__brand", "ram__category",
                "gpu__brand", "gpu__category",
                "psu__brand", "psu__category",
                "cooler__brand", "cooler__category",
                "storage__brand", "storage__category",
                "case__brand", "case__category",
                "case_fan__brand", "case_fan__category",

                # specs
                "cpu__cpu_spec",
                "motherboard__motherboard_spec",
                "ram__ram_spec",
                "gpu__gpu_spec",
                "psu__psu_spec",
                "cooler__cooler_spec",
                "storage__storage_spec",
                "case__case_spec",
                "case_fan__casefan_spec",
            ),
            id=item_id
        )

        serializer = CartItemReadSerializer(cart_item)
        return Response(serializer.data)
    

class UpdateBuildStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, item_id):
        user = request.user

        # 🔒 Only workers allowed
        if user.role != "worker":
            return Response({"detail": "Only workers allowed"}, status=403)

        status_value = request.data.get("status")

        if status_value not in ["accepted", "rejected"]:
            return Response({"detail": "Invalid status"}, status=400)

        cart_item = get_object_or_404(CartItem, id=item_id)

        cart_item.status = status_value
        cart_item.save()

        return Response({
            "message": f"Build {status_value}",
            "status": cart_item.status,
            "item_id": cart_item.id
        })