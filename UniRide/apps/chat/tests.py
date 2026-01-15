from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from apps.users.models import User, Role
from apps.trips.models import Publication, PublicationType, TripStatus, TripPassengerStatus
from apps.chat.models import Chat, Message
import datetime

class ChatLogicTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create Roles
        self.role_user = Role.objects.create(name='Usuario')
        
        # Create Statuses needed for flow
        TripStatus.objects.get_or_create(name='Pendiente')
        TripPassengerStatus.objects.get_or_create(name='Pendiente')
        
        # Create Users
        self.user1 = User.objects.create_user(username='user1', email='user1@ucundinamarca.edu.co', password='password123', name='User One', role_id=self.role_user)
        self.user2 = User.objects.create_user(username='user2', email='user2@ucundinamarca.edu.co', password='password123', name='User Two', role_id=self.role_user)
        self.user3 = User.objects.create_user(username='user3', email='user3@ucundinamarca.edu.co', password='password123', name='User Three', role_id=self.role_user)
        
        # Create Publication Types
        self.type_offer = PublicationType.objects.create(name='Oferta')
        self.type_request = PublicationType.objects.create(name='Solicitud')
        
        # Create Publications
        # Pub 1: Offer by User 1
        self.pub_offer = Publication.objects.create(
            user_id=self.user1,
            type_id=self.type_offer,
            departure_place="Place A",
            destination="Place B",
            departure_datetime=timezone.now() + datetime.timedelta(days=1),
            lat_departure_place=1.0,
            lon_departure_place=1.0,
            lat_destination=2.0,
            lon_destination=2.0,
            available_seats=3
        )
        
        # Pub 2: Request by User 2
        self.pub_request = Publication.objects.create(
            user_id=self.user2,
            type_id=self.type_request,
            departure_place="Place C",
            destination="Place D",
            departure_datetime=timezone.now() + datetime.timedelta(days=1),
            lat_departure_place=3.0,
            lon_departure_place=3.0,
            lat_destination=4.0,
            lon_destination=4.0,
            available_seats=1
        )

    def test_create_chat_offer_logic(self):
        """
        En Oferta: Dueño (User1) es Conductor. Interesado (User2) es Pasajero.
        User2 inicia el chat.
        """
        self.client.force_authenticate(user=self.user2)
        response = self.client.post('/api/chat/chats/', {'publication_id': self.pub_offer.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        chat = Chat.objects.get(id=response.data['id'])
        self.assertEqual(chat.driver, self.user1) # Dueño de oferta es conductor
        self.assertEqual(chat.passenger, self.user2) # Quien inicia es pasajero

    def test_create_chat_request_logic(self):
        """
        En Solicitud: Dueño (User2) es Pasajero. Interesado (User1) es Conductor.
        User1 inicia el chat.
        """
        self.client.force_authenticate(user=self.user1)
        response = self.client.post('/api/chat/chats/', {'publication_id': self.pub_request.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        chat = Chat.objects.get(id=response.data['id'])
        self.assertEqual(chat.passenger, self.user2) # Dueño de solicitud es pasajero
        self.assertEqual(chat.driver, self.user1) # Quien inicia es conductor

    def test_create_duplicate_chat(self):
        # Crear primer chat
        self.client.force_authenticate(user=self.user2)
        resp1 = self.client.post('/api/chat/chats/', {'publication_id': self.pub_offer.id})
        self.assertEqual(resp1.status_code, status.HTTP_201_CREATED)
        
        # Intentar crear de nuevo (Idempotente)
        resp2 = self.client.post('/api/chat/chats/', {'publication_id': self.pub_offer.id})
        self.assertEqual(resp2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp1.data['id'], resp2.data['id'])

    def test_only_participants_access(self):
        # Crear chat entre User1 y User2
        chat = Chat.objects.create(publication=self.pub_offer, driver=self.user1, passenger=self.user2)
        
        # User3 intenta acceder
        self.client.force_authenticate(user=self.user3)
        response = self.client.get(f'/api/chat/chats/{chat.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND) # O 403 dependiendo de DRF config default

    def test_send_message(self):
        chat = Chat.objects.create(publication=self.pub_offer, driver=self.user1, passenger=self.user2)
        
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(f'/api/chat/chats/{chat.id}/messages/', {'content': 'Hola'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Message.objects.count(), 1)
        self.assertEqual(Message.objects.first().sender_id, self.user1)

    def test_close_chat_permissions(self):
        chat = Chat.objects.create(publication=self.pub_offer, driver=self.user1, passenger=self.user2)
        
        # Pasajero intenta cerrar
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(f'/api/chat/chats/{chat.id}/close/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Conductor cierra
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(f'/api/chat/chats/{chat.id}/close/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        chat.refresh_from_db()
        self.assertFalse(chat.is_active)

    def test_message_in_closed_chat(self):
        chat = Chat.objects.create(publication=self.pub_offer, driver=self.user1, passenger=self.user2, is_active=False)
        
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(f'/api/chat/chats/{chat.id}/messages/', {'content': 'Hola'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
