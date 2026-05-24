import secrets
from unittest.mock import patch

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from apps.users.models import User, Role


class LoginViewTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.role = Role.objects.create(
            id=2,
            name="Usuario"
        )

    def setUp(self):
        self.url = "/api/users/Login/"

        self.password = "Password123*"

        self.user = User.objects.create_user(
            email="user@test.com",
            username="user@test.com",
            password=self.password,
            role_id_id=2,
            is_active=True
        )

    def test_login_correcto(self):
        response = self.client.post(self.url, {
            "email": "user@test.com",
            "password": self.password
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.data)

    def test_login_password_incorrecta(self):
        response = self.client.post(self.url, {
            "email": "user@test.com",
            "password": "incorrecta"
        })

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.data["error"],
            "Credenciales inválidas"
        )

    def test_login_usuario_no_existe(self):
        response = self.client.post(self.url, {
            "email": "fake@test.com",
            "password": "123"
        })

        self.assertEqual(response.status_code, 401)

    @patch("apps.users.views.check_and_handle_suspension")
    def test_login_usuario_suspendido(self, mock_suspension):

        mock_suspension.return_value = {
            "is_permanent": True,
            "remaining_days": None,
            "reason": "Mal comportamiento"
        }

        response = self.client.post(self.url, {
            "email": "user@test.com",
            "password": self.password
        })

        self.assertEqual(response.status_code, 403)

    @patch("apps.users.views.decrypt_login_payload")
    def test_payload_invalido(self, mock_decrypt):

        mock_decrypt.side_effect = Exception("Payload inválido")

        response = self.client.post(self.url, {
            "payload": "abc"
        })

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["error"],
            "Payload de login inválido"
        )