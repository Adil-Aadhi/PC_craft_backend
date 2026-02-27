import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from products.models import Product, Brand, Category

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="StrongPass123!",
        role="user"
    )


@pytest.fixture
def worker(db):
    return User.objects.create_user(
        username="worker",
        email="worker@example.com",
        password="StrongPass123!",
        role="worker"
    )


@pytest.fixture
def brand(db):
    return Brand.objects.create(name="AMD")


@pytest.fixture
def category(db):
    return Category.objects.create(name="CPU")


@pytest.fixture
def product(db, brand, category):
    return Product.objects.create(
        name="Ryzen 5 5600X",
        model_number="5600X",
        price=15000,
        stock_quantity=10,
        brand=brand,
        category=category
    )