from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from users.models import Address

User = get_user_model()


class UserAddressAPITest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="addressuser",
            email="test@example.com",
            password="password123",
            role="user"
        )
        self.client.force_authenticate(user=self.user)

        self.address1 = Address.objects.create(
            user=self.user,
            full_name="John Doe",
            phone="9999999999",
            address_line="Street 1",
            city="City",
            state="State",
            pincode="123456",
            is_default=True
        )

        self.address2 = Address.objects.create(
            user=self.user,
            full_name="Jane Doe",
            phone="8888888888",
            address_line="Street 2",
            city="City",
            state="State",
            pincode="654321",
            is_default=False
        )

    # ---------------- GET ----------------

    def test_list_user_addresses(self):
        url = reverse("user_address")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    # ---------------- POST ----------------

    def test_create_address(self):
        url = reverse("user_address")
        data = {
            "full_name": "New User",
            "phone": "7777777777",
            "address_line": "New Street",
            "city": "City",
            "state": "State",
            "pincode": "111111",
            "is_default": False
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Address.objects.count(), 3)

    def test_create_default_address_unsets_old_default(self):
        url = reverse("user_address")
        data = {
            "full_name": "Default User",
            "phone": "6666666666",
            "address_line": "Default Street",
            "city": "City",
            "state": "State",
            "pincode": "222222",
            "is_default": True
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.address1.refresh_from_db()
        self.assertFalse(self.address1.is_default)

    # ---------------- PUT ----------------

    def test_update_address(self):
        url = reverse("update_user_address", args=[self.address1.id])
        data = {
            "full_name": "Updated Name",
            "phone": "9999999999",
            "address_line": "Updated Street",
            "city": "City",
            "state": "State",
            "pincode": "123456",
            "is_default": True
        }

        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.address1.refresh_from_db()
        self.assertEqual(self.address1.full_name, "Updated Name")

    def test_update_address_not_found(self):
        url = reverse("update_user_address", args=[999])
        response = self.client.put(url, {})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ---------------- DELETE ----------------

    def test_delete_address(self):
        url = reverse("update_user_address", args=[self.address2.id])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Address.objects.count(), 1)

    def test_delete_default_address_sets_new_default(self):
        url = reverse("update_user_address", args=[self.address1.id])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        new_default = Address.objects.first()
        self.assertTrue(new_default.is_default)

    # ---------------- PATCH ----------------

    def test_set_default_address(self):
        url = reverse("default_user_address", args=[self.address2.id])
        response = self.client.patch(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.address1.refresh_from_db()
        self.address2.refresh_from_db()

        self.assertFalse(self.address1.is_default)
        self.assertTrue(self.address2.is_default)

    def test_set_default_address_not_found(self):
        url = reverse("default_user_address", args=[999])
        response = self.client.patch(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ---------------- AUTH ----------------

    def test_unauthorized_access(self):
        self.client.force_authenticate(user=None)
        url = reverse("user_address")
        response = self.client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
