# apps/users/tests/test_logout.py

import secrets

from rest_framework.test import APITestCase
from rest_framework import status

from apps.users.models import User, Role


class LogoutTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        Role.objects.create(id=2, name="Usuario")

    def setUp(self):

        self.user = User.objects.create_user(
            email="test@test.com",
            username="test@test.com",
            password="Password123*",
            role_id_id=2
        )

        self.client.force_authenticate(user=self.user)

        self.url = "/api/users/Logout/"

    def test_logout_correcto(self):

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["message"],
            "Logout exitoso"
        )