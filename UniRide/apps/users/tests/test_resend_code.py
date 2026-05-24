from unittest.mock import patch
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status

from apps.users.models import PendingUser


class ResendCodeTests(APITestCase):

    def setUp(self):
        self.url = "/api/users/register/resend-verification-code/"

    @patch("apps.users.views.send_code_email")  # 🔥 ESTE ES EL CLAVE
    def test_reenvio_correcto(self, mock_send_email):

        PendingUser.objects.create(
            name="Test User",
            email="test@test.com",
            phone="3001234567",
            password="hashed",
            code="123456",
            expires_at=timezone.now()
        )

        response = self.client.post(
            self.url,
            {"email": "test@test.com"},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_send_email.assert_called_once()

    def test_pending_no_existe(self):

        response = self.client.post(
            self.url,
            {"email": "noexiste@test.com"},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)