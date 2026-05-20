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
    TripPassengerStatus,
    TripPassenger,
)
from apps.chat.models import Chat, Message


# ==============================
# CONSTANTES
# ==============================
CHAT_BASE_URL = "/api/chat/chats/"


class PublicationTypeEnum:
    OFFER = "Oferta"
    REQUEST = "Solicitud"


# ==============================
# FACTORIES
# ==============================
def create_user(username, role):
    return User.objects.create_user(
        username=username,
        email=f"{username}@ucundinamarca.edu.co",
        password="password123",
        name=f"{username}",
        role_id=role,
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
        available_seats=seats,
    )


# ==============================
# BASE TEST CASE
# ==============================
class ChatBaseTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.role_user = Role.objects.create(name="Usuario")

        TripStatus.objects.get_or_create(name="Pendiente")
        TripPassengerStatus.objects.get_or_create(name="Pendiente")

        self.user1 = create_user("user1", self.role_user)
        self.user2 = create_user("user2", self.role_user)
        self.user3 = create_user("user3", self.role_user)

        self.type_offer = PublicationType.objects.create(name=PublicationTypeEnum.OFFER)
        self.type_request = PublicationType.objects.create(name=PublicationTypeEnum.REQUEST)

        self.pub_offer = create_publication(
            self.user1, self.type_offer, "Place A", "Place B", seats=3
        )
        self.pub_request = create_publication(
            self.user2, self.type_request, "Place C", "Place D", seats=1
        )

    def _create_chat(self, driver=None, passenger=None, publication=None, is_active=True):
        return Chat.objects.create(
            publication=publication or self.pub_offer,
            driver=driver or self.user1,
            passenger=passenger or self.user2,
            is_active=is_active,
        )


# ======================================================
# 1. CREACIÓN DE CHAT
# ======================================================
class ChatCreateTests(ChatBaseTestCase):

    def test_create_chat_offer_logic(self):
        """Oferta → dueño es conductor, quien inicia es pasajero."""
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(CHAT_BASE_URL, {"publication_id": self.pub_offer.id})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        chat = Chat.objects.get(id=response.data["id"])
        self.assertEqual(chat.driver, self.user1)
        self.assertEqual(chat.passenger, self.user2)

    def test_create_chat_request_logic(self):
        """Solicitud → dueño es pasajero, quien inicia es conductor."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(CHAT_BASE_URL, {"publication_id": self.pub_request.id})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        chat = Chat.objects.get(id=response.data["id"])
        self.assertEqual(chat.passenger, self.user2)
        self.assertEqual(chat.driver, self.user1)

    def test_create_chat_idempotente(self):
        """Crear el mismo chat dos veces devuelve el mismo objeto."""
        self.client.force_authenticate(user=self.user2)
        resp1 = self.client.post(CHAT_BASE_URL, {"publication_id": self.pub_offer.id})
        resp2 = self.client.post(CHAT_BASE_URL, {"publication_id": self.pub_offer.id})

        self.assertEqual(resp1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp1.data["id"], resp2.data["id"])

    def test_create_chat_sin_autenticacion(self):
        """Sin token → 401."""
        response = self.client.post(CHAT_BASE_URL, {"publication_id": self.pub_offer.id})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_chat_publicacion_inexistente(self):
        """Publicación que no existe → error de validación."""
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(CHAT_BASE_URL, {"publication_id": 99999})
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND])

    def test_create_chat_sin_publication_id(self):
        """Sin publication_id → 400."""
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(CHAT_BASE_URL, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_dueno_no_puede_crear_chat_consigo_mismo(self):
        """El dueño de la publicación no puede abrir chat con sí mismo."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(CHAT_BASE_URL, {"publication_id": self.pub_offer.id})
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN])


# ======================================================
# 2. LISTADO DE CHATS
# ======================================================
class ChatListTests(ChatBaseTestCase):

    def test_listar_chats_solo_propios(self):
        """El usuario solo ve sus chats (como driver o passenger)."""
        self._create_chat(driver=self.user1, passenger=self.user2)
        self._create_chat(
            driver=self.user1,
            passenger=self.user3,
            publication=create_publication(self.user1, self.type_offer, "X", "Y"),
        )

        self.client.force_authenticate(user=self.user3)
        response = self.client.get(CHAT_BASE_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids_en_respuesta = [c["id"] for c in response.data]
        chats_de_user3 = Chat.objects.filter(passenger=self.user3)
        for chat in chats_de_user3:
            self.assertIn(chat.id, ids_en_respuesta)

    def test_listar_chats_sin_autenticacion(self):
        """Sin token → 401."""
        response = self.client.get(CHAT_BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_listar_chats_vacio(self):
        """Usuario sin chats recibe lista vacía."""
        self.client.force_authenticate(user=self.user3)
        response = self.client.get(CHAT_BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)


# ======================================================
# 3. DETALLE DE CHAT
# ======================================================
class ChatDetailTests(ChatBaseTestCase):

    def test_retrieve_chat_participante(self):
        """Participante puede ver el detalle del chat."""
        chat = self._create_chat()
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(f"{CHAT_BASE_URL}{chat.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], chat.id)

    def test_retrieve_chat_no_participante(self):
        """Tercero no puede ver el chat → 404."""
        chat = self._create_chat()
        self.client.force_authenticate(user=self.user3)
        response = self.client.get(f"{CHAT_BASE_URL}{chat.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_chat_inexistente(self):
        """Chat que no existe → 404."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(f"{CHAT_BASE_URL}99999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ======================================================
# 4. CIERRE DE CHAT
# ======================================================
class ChatCloseTests(ChatBaseTestCase):

    def test_conductor_puede_cerrar(self):
        """Solo el conductor puede cerrar el chat."""
        chat = self._create_chat()
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(f"{CHAT_BASE_URL}{chat.id}/close/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        chat.refresh_from_db()
        self.assertFalse(chat.is_active)
        self.assertIsNotNone(chat.closed_at)

    def test_pasajero_no_puede_cerrar(self):
        """Pasajero intenta cerrar → 403."""
        chat = self._create_chat()
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(f"{CHAT_BASE_URL}{chat.id}/close/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cerrar_chat_ya_cerrado(self):
        """Cerrar un chat que ya está cerrado → 400."""
        chat = self._create_chat(is_active=False)
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(f"{CHAT_BASE_URL}{chat.id}/close/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_tercero_no_puede_cerrar(self):
        """Tercero ajeno al chat no puede cerrarlo → 404."""
        chat = self._create_chat()
        self.client.force_authenticate(user=self.user3)
        response = self.client.post(f"{CHAT_BASE_URL}{chat.id}/close/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ======================================================
# 5. MENSAJES — GET
# ======================================================
class ChatMessagesGetTests(ChatBaseTestCase):

    def test_listar_mensajes_orden_cronologico(self):
        """Los mensajes se devuelven del más antiguo al más nuevo."""
        chat = self._create_chat()
        now = timezone.now()
        Message.objects.create(
            chat_id=chat, sender_id=self.user1, content="Primero",
            sent_at=now - datetime.timedelta(minutes=5)
        )
        Message.objects.create(
            chat_id=chat, sender_id=self.user2, content="Segundo",
            sent_at=now
        )

        self.client.force_authenticate(user=self.user1)
        response = self.client.get(f"{CHAT_BASE_URL}{chat.id}/messages/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["content"], "Primero")
        self.assertEqual(response.data[1]["content"], "Segundo")

    def test_listar_mensajes_chat_vacio(self):
        """Chat sin mensajes devuelve lista vacía."""
        chat = self._create_chat()
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(f"{CHAT_BASE_URL}{chat.id}/messages/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_listar_mensajes_no_participante(self):
        """Tercero no puede ver mensajes → 404."""
        chat = self._create_chat()
        self.client.force_authenticate(user=self.user3)
        response = self.client.get(f"{CHAT_BASE_URL}{chat.id}/messages/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ======================================================
# 6. MENSAJES — POST
# ======================================================
class ChatMessagesPostTests(ChatBaseTestCase):

    def test_enviar_mensaje_conductor(self):
        """Conductor puede enviar mensaje en chat activo."""
        chat = self._create_chat()
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(
            f"{CHAT_BASE_URL}{chat.id}/messages/", {"content": "Hola"}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Message.objects.count(), 1)
        self.assertEqual(Message.objects.first().sender_id, self.user1)

    def test_enviar_mensaje_pasajero(self):
        """Pasajero puede enviar mensaje en chat activo."""
        chat = self._create_chat()
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(
            f"{CHAT_BASE_URL}{chat.id}/messages/", {"content": "Hola desde pasajero"}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_enviar_mensaje_chat_cerrado(self):
        """No se pueden enviar mensajes en chat cerrado → 400."""
        chat = self._create_chat(is_active=False)
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(
            f"{CHAT_BASE_URL}{chat.id}/messages/", {"content": "Hola"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_enviar_mensaje_sin_contenido(self):
        """Mensaje vacío → 400."""
        chat = self._create_chat()
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(
            f"{CHAT_BASE_URL}{chat.id}/messages/", {"content": ""}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_enviar_mensaje_sin_autenticacion(self):
        """Sin token → 401."""
        chat = self._create_chat()
        response = self.client.post(
            f"{CHAT_BASE_URL}{chat.id}/messages/", {"content": "Hola"}
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_enviar_mensaje_no_participante(self):
        """Tercero no puede enviar mensaje → 404."""
        chat = self._create_chat()
        self.client.force_authenticate(user=self.user3)
        response = self.client.post(
            f"{CHAT_BASE_URL}{chat.id}/messages/", {"content": "Intruso"}
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_mensaje_con_trip_passenger_rechazado(self):
        """No se pueden enviar mensajes si trip_passenger está Rechazado → 409."""
        from apps.trips.models import Trip

        status_rechazado, _ = TripPassengerStatus.objects.get_or_create(name="Rechazado")
        trip_status, _ = TripStatus.objects.get_or_create(name="Pendiente")

        trip = Trip.objects.create(
            publication_id=self.pub_offer,
            driver_id=self.user1,
            status_id=trip_status,
        )

        trip_passenger = TripPassenger.objects.create(
            trip_id=trip,
            passenger_id=self.user2,
            status_id=status_rechazado,
            seats_reserved=1,
        )

        chat = Chat.objects.create(
            publication=self.pub_offer,
            driver=self.user1,
            passenger=self.user2,
            is_active=True,
            trip_passenger=trip_passenger,
        )

        self.client.force_authenticate(user=self.user1)
        response = self.client.post(
            f"{CHAT_BASE_URL}{chat.id}/messages/", {"content": "¿Sigues ahí?"}
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)