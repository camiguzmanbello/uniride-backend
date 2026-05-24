# apps/users/tests/test_verify_pending.py

from datetime import timedelta
from unittest.mock import patch

from django.utils import timezone

from rest_framework.test import APITestCase

from apps.users.models import (
    PendingUser,
    Role,
    User
)


class VerifyPendingTests(APITestCase):

    @classmethod
    def setUpTestData(cls):

        cls.admin_role = Role.objects.create(
            id=1,
            name="Administrador"
        )

        cls.user_role = Role.objects.create(
            id=2,
            name="Usuario"
        )

    def setUp(self):

        self.url = "/api/users/verify-pending/"

        self.pending = PendingUser.objects.create(
            name="Test",
            email="test@test.com",
            phone="3000000000",
            password="hashed",
            role_id=self.user_role,
            code="123456",
            expires_at=timezone.now() + timedelta(minutes=10)
        )

    def test_codigo_invalido(self):

        response = self.client.post(
            self.url,
            {
                "code": "999999"
            }
        )

        self.assertEqual(
            response.status_code,
            400
        )

    @patch("cloudinary.uploader.upload")
    def test_verificacion_correcta(self, mock_upload):

        mock_upload.return_value = {
            "secure_url": "https://img.com/test.png"
        }

        response = self.client.post(
            self.url,
            {
                "code": "123456"
            }
        )

        self.assertEqual(
            response.status_code,
            201
        )

        self.assertTrue(
            User.objects.filter(
                email="test@test.com"
            ).exists()
        )