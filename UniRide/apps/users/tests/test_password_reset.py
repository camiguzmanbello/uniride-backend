# apps/users/tests/test_password_reset.py

import secrets
from unittest.mock import patch

from rest_framework.test import APITestCase

from apps.users.models import User, Role


class PasswordResetRequestTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        Role.objects.create(id=2, name="Usuario")

    def setUp(self):

        self.url = "/api/users/auth/request-password-reset/"

        self.user = User.objects.create_user(
            email="user@test.com",
            username="user@test.com",
            password="Password123*",
            role_id_id=2
        )

    def test_email_requerido(self):

        response = self.client.post(self.url, {})

        self.assertEqual(response.status_code, 400)

    def test_usuario_no_existe(self):

        response = self.client.post(self.url, {
            "email": "fake@test.com"
        })

        self.assertEqual(response.status_code, 404)

    @patch("apps.users.views.send_code_email")
    def test_password_reset_ok(self, mock_send):

        response = self.client.post(self.url, {
            "email": "user@test.com"
        })

        self.assertEqual(response.status_code, 200)

    @patch("apps.users.views.send_code_email")
    def test_error_enviando_correo(self, mock_send):

        mock_send.side_effect = Exception("SMTP ERROR")

        response = self.client.post(self.url, {
            "email": "user@test.com"
        })

        self.assertEqual(response.status_code, 503)