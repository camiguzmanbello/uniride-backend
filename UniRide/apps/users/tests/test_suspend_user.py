# apps/users/tests/test_suspend_user.py

from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import (
    User,
    Role
)

from apps.complaints.models import (
    Complaint,
    ComplaintStatus,
    ComplaintType
)


class SuspendUserTests(APITestCase):

    @classmethod
    def setUpTestData(cls):

        # Roles
        cls.admin_role = Role.objects.create(
            id=1,
            name="Administrador"
        )

        cls.user_role = Role.objects.create(
            id=2,
            name="Usuario"
        )

        # Estados requeridos por el endpoint
        cls.pending_status = ComplaintStatus.objects.create(
            id=1,
            name="Pendiente"
        )

        cls.resolved_status = ComplaintStatus.objects.create(
            id=2,
            name="Resuelta"
        )

        cls.rejected_status = ComplaintStatus.objects.create(
            id=3,
            name="Rechazada"
        )

        cls.in_review_status = ComplaintStatus.objects.create(
            id=4,
            name="En revisión"
        )

        # Tipo
        cls.complaint_type = ComplaintType.objects.create(
            id=1,
            name="Conducta inapropiada"
        )

    def setUp(self):

        # Admin
        self.admin = User.objects.create_user(
            email="admin@test.com",
            username="admin@test.com",
            password="Password123*",
            is_staff=True,
            role_id_id=self.admin_role.id
        )

        # Usuario reportado
        self.user = User.objects.create_user(
            email="user@test.com",
            username="user@test.com",
            password="Password123*",
            role_id_id=self.user_role.id
        )

        # Reportante
        self.reporter = User.objects.create_user(
            email="reporter@test.com",
            username="reporter@test.com",
            password="Password123*",
            role_id_id=self.user_role.id
        )

        self.client.force_authenticate(
            user=self.admin
        )

        self.url = (
            f"/api/users/admin/suspend-user/{self.user.id}/"
        )

    def test_sin_quejas(self):

        response = self.client.post(
            self.url,
            {
                "reason": "Spam"
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_sin_reason(self):

        response = self.client.post(
            self.url,
            {
                "complaint_ids": [1]
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    @patch("apps.users.views.send_suspension_email")
    def test_suspend_correctamente(
        self,
        mock_email
    ):

        complaint = Complaint.objects.create(
            reporter_id_id=self.reporter.id,
            reported_user_id_id=self.user.id,
            type_id_id=self.complaint_type.id,
            status_id_id=self.pending_status.id,
            admin_id_id=self.admin.id,
            trip_id=None,
            description="Usuario con comportamiento inapropiado"
        )

        response = self.client.post(
            self.url,
            {
                "complaint_ids": [complaint.id],
                "reason": "Mal comportamiento",
                "is_permanent": True
            },
            format="json"
        )

        print(response.data)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.user.refresh_from_db()

        self.assertTrue(
            self.user.is_suspended
        )

        mock_email.assert_called_once()