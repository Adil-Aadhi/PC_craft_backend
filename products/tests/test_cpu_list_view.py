import pytest
from django.urls import reverse
from rest_framework import status

from products.models import Product, Category, Brand


@pytest.fixture
def cpu_category(db):
    return Category.objects.create(name="CPU")


@pytest.fixture
def brand(db):
    return Brand.objects.create(name="AMD")


@pytest.fixture
def cpu_products(db, cpu_category, brand):
    products = []

    products.append(Product.objects.create(
        name="CPU 15K",
        price=15000,
        category=cpu_category,
        brand=brand,
        stock_quantity=10,
        is_active=True,
        is_deleted=False
    ))

    products.append(Product.objects.create(
        name="CPU 30K",
        price=30000,
        category=cpu_category,
        brand=brand,
        stock_quantity=10,
        is_active=True,
        is_deleted=False
    ))

    products.append(Product.objects.create(
        name="CPU 60K",
        price=60000,
        category=cpu_category,
        brand=brand,
        stock_quantity=10,
        is_active=True,
        is_deleted=False
    ))

    # inactive product (should not appear)
    Product.objects.create(
        name="Inactive CPU",
        price=10000,
        category=cpu_category,
        brand=brand,
        stock_quantity=10,
        is_active=False,
        is_deleted=False
    )

    return products

@pytest.mark.django_db
class TestCPUListView:

    def test_list_cpus(self, api_client, cpu_products):
        url = reverse("pc-cpu")  # adjust name

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 3  # only active products

    def test_search_filter(self, api_client, cpu_products):
        url = reverse("pc-cpu")

        response = api_client.get(url, {"search": "30K"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["name"] == "CPU 30K"

    def test_price_filter_lt20(self, api_client, cpu_products):
        url = reverse("pc-cpu")

        response = api_client.get(url, {"price": "lt20"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["price"] == "15000.00"

    def test_price_filter_20to50(self, api_client, cpu_products):
        url = reverse("pc-cpu")

        response = api_client.get(url, {"price": "20to50"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["price"] == "30000.00"

    def test_price_filter_gt50(self, api_client, cpu_products):
        url = reverse("pc-cpu")

        response = api_client.get(url, {"price": "gt50"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["price"] == "60000.00"

    def test_pagination(self, api_client, cpu_products):
        url = reverse("pc-cpu")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 3
        assert len(response.data["results"]) == 3