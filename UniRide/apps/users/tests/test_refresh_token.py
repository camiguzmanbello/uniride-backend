# apps/users/tests/test_refresh_token.py

from rest_framework.test import APITestCase
from rest_framework import status


class RefreshTokenTests(APITestCase):

    def setUp(self):
        self.url = "/api/users/Refresh-token/"

    def test_refresh_sin_cookie(self):

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 401)

    def test_refresh_token_invalido(self):

        self.client.cookies["refresh_token"] = "token_fake"

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.data["error"],
            "Token inválido o expirado"
        )