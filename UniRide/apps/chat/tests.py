from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
import datetime

from apps.users.models import User, Role
from apps.trips.models import (
    Publication, 
    PublicationType, 
    TripStatus, 
    TripPassengerStatus
)
from apps.chat.models import Chat, Message


# ==============================
# CONSTANTES (EVITA DUPLICACIÓN)
# ==============================
CHAT_BASE_URL = '/api/chat/chats/'


class PublicationTypeEnum:
    OFFER = "Oferta"
    REQUEST = "Solicitud"


# ==============================
# FACTORIES (REUTILIZACIÓN)
# ==============================
def create_user(username, role):
    return User.objects.create_user(
        username=username,
        email=f"{username}@ucundinamarca.edu.co",
        password="password123",
        name=f"{username}",
        role_id=role
    )


def create_publication(user, publication_type, departure, destination, seats=1):
    return Publication.objects.create(
        user_id=user,
        type_id=publication_type,
        departure_place=departure,
        destination=destination,
        departure_datetime=timezone.now() + datetime.timedelta(days=1),
        lat_departure_place=1.0,
        lon_departure_place=1.0,
        lat_destination=2.0,
        lon_destination=2.0,
        available_seats=seats
    )


# ==============================
# TEST CASE
# ==============================
class ChatLogicTestCase(TestCase):

    def setUp(self):
        self.client = APIClient()

        # Roles
        self.role_user = Role.objects.create(name='Usuario')

        # Estados requeridos
        TripStatus.objects.get_or_create(name='Pendiente')
        TripPassengerStatus.objects.get_or_create(name='Pendiente')

        # Usuarios
        self.user1 = create_user('user1', self.role_user)
        self.user2 = create_user('user2', self.role_user)
        self.user3 = create_user('user3', self.role_user)

        # Tipos de publicación
        self.type_offer = PublicationType.objects.create(name=PublicationTypeEnum.OFFER)
        self.type_request = PublicationType.objects.create(name=PublicationTypeEnum.REQUEST)

        # Publicaciones
        self.pub_offer = create_publication(
            self.user1, self.type_offer, "Place A", "Place B", seats=3
        )

        self.pub_request = create_publication(
            self.user2, self.type_request, "Place C", "Place D", seats=1
        )

    # ==========================================
    # CREACIÓN DE CHAT (LÓGICA DE NEGOCIO)
    # ==========================================

    def test_create_chat_offer_logic(self):
        """
        Regla:
        - Si es Oferta → dueño = conductor
        - Usuario que inicia → pasajero
        """
        self.client.force_authenticate(user=self.user2)

        response = self.client.post(CHAT_BASE_URL, {
            'publication_id': self.pub_offer.id
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        chat = Chat.objects.get(id=response.data['id'])

        self.assertEqual(chat.driver, self.user1)
        self.assertEqual(chat.passenger, self.user2)

    def test_create_chat_request_logic(self):
        """
        Regla:
        - Si es Solicitud → dueño = pasajero
        - Usuario que inicia → conductor
        """
        self.client.force_authenticate(user=self.user1)

        response = self.client.post(CHAT_BASE_URL, {
            'publication_id': self.pub_request.id
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        chat = Chat.objects.get(id=response.data['id'])

        self.assertEqual(chat.passenger, self.user2)
        self.assertEqual(chat.driver, self.user1)

    # ==========================================
    # IDEMPOTENCIA
    # ==========================================

    def test_create_duplicate_chat(self):
        self.client.force_authenticate(user=self.user2)

        resp1 = self.client.post(CHAT_BASE_URL, {
            'publication_id': self.pub_offer.id
        })

        self.assertEqual(resp1.status_code, status.HTTP_201_CREATED)

        resp2 = self.client.post(CHAT_BASE_URL, {
            'publication_id': self.pub_offer.id
        })

        self.assertEqual(resp2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp1.data['id'], resp2.data['id'])

    # ==========================================
    # SEGURIDAD
    # ==========================================

    def test_only_participants_access(self):
        chat = Chat.objects.create(
            publication=self.pub_offer,
            driver=self.user1,
            passenger=self.user2
        )

        self.client.force_authenticate(user=self.user3)

        response = self.client.get(f"{CHAT_BASE_URL}{chat.id}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ==========================================
    # MENSAJES
    # ==========================================

    def test_send_message(self):
        chat = Chat.objects.create(
            publication=self.pub_offer,
            driver=self.user1,
            passenger=self.user2
        )

        self.client.force_authenticate(user=self.user1)

        response = self.client.post(
            f"{CHAT_BASE_URL}{chat.id}/messages/",
            {'content': 'Hola'}
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Message.objects.count(), 1)
        self.assertEqual(Message.objects.first().sender_id, self.user1)

    # ==========================================
    # CIERRE DE CHAT
    # ==========================================

    def test_close_chat_permissions(self):
        chat = Chat.objects.create(
            publication=self.pub_offer,
            driver=self.user1,
            passenger=self.user2
        )

        # Pasajero no puede cerrar
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(f"{CHAT_BASE_URL}{chat.id}/close/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Conductor sí puede cerrar
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(f"{CHAT_BASE_URL}{chat.id}/close/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        chat.refresh_from_db()
        self.assertFalse(chat.is_active)

    # ==========================================
    # CHAT CERRADO
    # ==========================================

    def test_message_in_closed_chat(self):
        chat = Chat.objects.create(
            publication=self.pub_offer,
            driver=self.user1,
            passenger=self.user2,
            is_active=False
        )

        self.client.force_authenticate(user=self.user1)

        response = self.client.post(
            f"{CHAT_BASE_URL}{chat.id}/messages/",
            {'content': 'Hola'}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)