from django.utils import timezone
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import timedelta
import secrets
from apps.users.models import PendingUser, User, Role


class ConfirmAdminViewTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        """
        Crear Roles sin depender del nombre exacto de los campos.
        Si el modelo tiene campos obligatorios, debes mostrármelo.
        """
        cls.admin_role = Role.objects.create(id=1)
        cls.client_role = Role.objects.create(id=2)

    def setUp(self):
        # Endpoint
        self.url = "/api/users/Admin/confirm/"

        # Datos base
        self.email = "admin@test.com"
        self.phone = "3000000000"
        self.code = "123456"
        self.password = secrets.token_urlsafe(12)

        # Actor: administrador que preregistró
        self.actor = User.objects.create_user(
            email="registrador@test.com",
            username="registrador@test.com",
            password=secrets.token_urlsafe(10),
            is_staff=True,
            role_id_id=1
        )

        # Preregistro válido
        self.pending = PendingUser.objects.create(
            name="Nuevo Admin",
            email=self.email,
            phone=self.phone,
            code=self.code,
            expires_at=timezone.now() + timedelta(minutes=10),
            role_id_id=1,
            registrado_por=self.actor,
        )

    # -------------------------------------------------------
    # VALIDACIONES DEL CÓDIGO
    # -------------------------------------------------------

    def test_codigo_solo_numeros(self):
        data = {"code": "ABC123", "password": self.password}
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"], "El código debe contener solo números.")

    def test_codigo_solo_6_digitos(self):
        data = {"code": "12345", "password": self.password}
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"], "El código debe tener exactamente 6 dígitos.")

    # -------------------------------------------------------
    # VALIDACIÓN DE EXISTENCIA DEL CÓDIGO
    # -------------------------------------------------------

    def test_codigo_invalido(self):
        data = {"code": "999999", "password": self.password}
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"], "Código inválido o expirado.")

    def test_codigo_expirado(self):
        # Hacer que ya venció
        self.pending.expires_at = timezone.now() - timedelta(minutes=1)
        self.pending.save()

        data = {"code": self.code, "password": self.password}
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"], "Código inválido o expirado.")

    # -------------------------------------------------------
    # RESTRICCIÓN DE ROL
    # -------------------------------------------------------

    def test_no_es_admin(self):
        # Cambiar preregistro a rol cliente
        self.pending.role_id_id = 2
        self.pending.save()

        data = {"code": self.code, "password": self.password}
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["error"], "No tienes permiso para confirmar esta cuenta.")

    # -------------------------------------------------------
    # CONFIRMACIÓN EXITOSA
    # -------------------------------------------------------

    def test_confirmacion_correcta_crea_usuario(self):
        data = {"code": self.code, "password": self.password}
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Cuenta de administrador confirmada con éxito.")

        # Validar creación del usuario
        user = User.objects.get(email=self.email)
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_staff)
        self.assertEqual(user.role_id_id, 1)

        # PendingUser debe desaparecer
        self.assertFalse(PendingUser.objects.filter(email=self.email).exists())

    # -------------------------------------------------------
    # USUARIO YA ACTIVO
    # -------------------------------------------------------

    def test_usuario_ya_activo(self):
        # Crear usuario activo ANTES de la confirmación
        User.objects.create_user(
            email=self.email,
            username=self.email,
            password=secrets.token_urlsafe(10),
            is_active=True,
            is_staff=True,
            role_id_id=1
        )

        data = {"code": self.code, "password": self.password}
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"], "Este usuario ya está activo.")
