import base64
import json
import os
import secrets
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.test import override_settings
from rest_framework.test import APITestCase

from apps.users.models import Role, User


def _encrypt_payload(public_key, email: str, password: str) -> dict:
    aes_key = os.urandom(32)
    iv = os.urandom(12)
    plaintext = json.dumps({"email": email, "password": password}).encode("utf-8")
    ciphertext = AESGCM(aes_key).encrypt(iv, plaintext, None)

    enc_key = public_key.encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )

    return {
        "v": 1,
        "alg": "RSA-OAEP-256+A256GCM",
        "enc_key": base64.b64encode(enc_key).decode("utf-8"),
        "iv": base64.b64encode(iv).decode("utf-8"),
        "ciphertext": base64.b64encode(ciphertext).decode("utf-8"),
    }


class LoginEncryptedPayloadTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        Role.objects.create(name="Cliente")

    def setUp(self):
        self.url = "/api/users/Login/"
        self.email = "user@test.com"
        # ⚠️ Test-only credential (no producción)
        self.password = secrets.token_urlsafe(12)
        self.user = User.objects.create_user(
            username=self.email,
            email=self.email,
            password=self.password,
            name="User",
            phone="3000000001",
        )

        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.public_key = self.private_key.public_key()

        self.private_pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")

        self.public_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")

    @override_settings(LOGIN_PAYLOAD_PRIVATE_KEY_PEM="")
    def test_login_plaintext_sigue_funcionando_sin_llaves(self):
        response = self.client.post(self.url, {"email": self.email, "password": self.password}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.cookies)
        self.assertIn("refresh_token", response.cookies)

    @override_settings()
    def test_login_encrypted_payload_funciona(self):
        with override_settings(LOGIN_PAYLOAD_PRIVATE_KEY_PEM=self.private_pem):
            payload = _encrypt_payload(self.public_key, self.email, self.password)
            response = self.client.post(self.url, {"payload": payload}, format="json")
            self.assertEqual(response.status_code, 200)
            self.assertIn("access_token", response.cookies)
            self.assertIn("refresh_token", response.cookies)

    @override_settings()
    def test_login_encrypted_payload_invalido_devuelve_400_generico(self):
        with override_settings(LOGIN_PAYLOAD_PRIVATE_KEY_PEM=self.private_pem):
            response = self.client.post(self.url, {"payload": {"v": 1, "alg": "RSA-OAEP-256+A256GCM"}}, format="json")
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.data.get("error"), "Payload de login inválido")

    @override_settings()
    def test_login_public_key_endpoint(self):
        url = "/api/users/login-public-key/"
        with override_settings(LOGIN_PAYLOAD_PRIVATE_KEY_PEM=self.private_pem, LOGIN_PAYLOAD_PUBLIC_KEY_PEM=""):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data.get("v"), 1)
            self.assertEqual(response.data.get("alg"), "RSA-OAEP-256+A256GCM")
            self.assertEqual(response.data.get("public_key_pem"), self.public_pem)
