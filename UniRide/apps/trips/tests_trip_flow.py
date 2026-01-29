from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from apps.users.models import User, Role, Vehicle, VehicleType
from apps.trips.models import Publication, PublicationType, Trip, TripPassenger, TripStatus, TripPassengerStatus
from apps.chat.models import Chat
import datetime

class TripFlowTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create Roles
        self.role_user = Role.objects.create(name='Usuario')
        
        # Create Users
        self.user1 = User.objects.create_user(username='user1', email='user1@ucundinamarca.edu.co', password='password123', name='User One', role_id=self.role_user)
        self.user2 = User.objects.create_user(username='user2', email='user2@ucundinamarca.edu.co', password='password123', name='User Two', role_id=self.role_user)
        self.user3 = User.objects.create_user(username='user3', email='user3@ucundinamarca.edu.co', password='password123', name='User Three', role_id=self.role_user)
        
        # Create Vehicle Type and Vehicle
        self.v_type_car = VehicleType.objects.create(name='Carro')
        self.vehicle1 = Vehicle.objects.create(
            user_id=self.user1,
            type_id=self.v_type_car,
            brand='Toyota',
            plate='ABC-123',
            is_active=True
        )

        # Create Publication Types
        self.type_offer = PublicationType.objects.create(name='Oferta')
        self.type_request = PublicationType.objects.create(name='Solicitud')
        
        # Create Statuses
        self.status_pending, _ = TripStatus.objects.get_or_create(name='Pendiente')
        self.tp_status_pending, _ = TripPassengerStatus.objects.get_or_create(name='Pendiente')
        self.tp_status_accepted, _ = TripPassengerStatus.objects.get_or_create(name='Aceptado')
        self.tp_status_rejected, _ = TripPassengerStatus.objects.get_or_create(name='Rechazado')
        self.tp_status_canceled, _ = TripPassengerStatus.objects.get_or_create(name='Cancelado')

        # Create Publication (Offer)
        self.pub_offer = Publication.objects.create(
            user_id=self.user1,
            type_id=self.type_offer,
            vehicle_id=self.vehicle1,
            departure_place="Place A",
            destination="Place B",
            departure_datetime=timezone.now() + datetime.timedelta(days=1),
            lat_departure_place=1.0,
            lon_departure_place=1.0,
            lat_destination=2.0,
            lon_destination=2.0,
            available_seats=1,
            is_active=True
        )

    def test_create_interest_flow(self):
        # User 2 shows interest
        self.client.force_authenticate(user=self.user2)
        response = self.client.post('/api/chat/interests/', {'publication_id': self.pub_offer.id, 'seats_reserved': 1})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        data = response.data
        self.assertIn('trip_passenger_id', data)
        self.assertIn('chat_id', data)
        
        # Check Trip Created
        trip = Trip.objects.get(publication_id=self.pub_offer.id)
        self.assertEqual(trip.driver_id, self.user1)
        
        # Check TripPassenger Created
        tp = TripPassenger.objects.get(id=data['trip_passenger_id'])
        self.assertEqual(tp.passenger_id, self.user2)
        self.assertEqual(tp.status_id.name, 'Pendiente')
        
        # Check Chat Created and Linked
        chat = Chat.objects.get(id=data['chat_id'])
        self.assertEqual(chat.trip_passenger, tp)
        self.assertTrue(chat.is_active)

    def test_create_interest_duplication(self):
        self.client.force_authenticate(user=self.user2)
        # First call
        resp1 = self.client.post('/api/chat/interests/', {'publication_id': self.pub_offer.id})
        chat_id1 = resp1.data['chat_id']
        
        # Second call
        resp2 = self.client.post('/api/chat/interests/', {'publication_id': self.pub_offer.id})
        self.assertEqual(resp2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp2.data['chat_id'], chat_id1) # Should return existing

    def test_accept_passenger_flow(self):
        # 1. Update available seats to 2 to test multiple acceptance
        self.pub_offer.available_seats = 2
        self.pub_offer.save()

        # 2. Create interest (User 2)
        self.client.force_authenticate(user=self.user2)
        resp = self.client.post('/api/chat/interests/', {'publication_id': self.pub_offer.id})
        tp_id = resp.data['trip_passenger_id']
        chat_id = resp.data['chat_id']
        
        # 3. Create interest (User 3) - Competition
        self.client.force_authenticate(user=self.user3)
        resp3 = self.client.post('/api/chat/interests/', {'publication_id': self.pub_offer.id})
        tp_id3 = resp3.data['trip_passenger_id']
        chat_id3 = resp3.data['chat_id']
        
        # 4. Accept User 2 (Driver User 1)
        self.client.force_authenticate(user=self.user1)
        resp_accept = self.client.post(f'/api/trips/trippassengers/{tp_id}/accept/')
        self.assertEqual(resp_accept.status_code, status.HTTP_200_OK)
        
        # Verify User 2 Accepted
        tp = TripPassenger.objects.get(id=tp_id)
        self.assertEqual(tp.status_id.name, 'Aceptado')
        
        # Verify Seats Decremented (2 -> 1)
        self.pub_offer.refresh_from_db()
        self.assertEqual(self.pub_offer.available_seats, 1)
        
        # Verify User 3 NOT Rejected (seats > 0)
        tp3 = TripPassenger.objects.get(id=tp_id3)
        self.assertEqual(tp3.status_id.name, 'Pendiente')
        
        # Verify User 2 Chat Still Active (new rule)
        chat = Chat.objects.get(id=chat_id)
        self.assertTrue(chat.is_active)
        
        # 5. Accept User 3 (Driver User 1)
        resp_accept3 = self.client.post(f'/api/trips/trippassengers/{tp_id3}/accept/')
        self.assertEqual(resp_accept3.status_code, status.HTTP_200_OK)
        
        # Verify Seats Decremented (1 -> 0)
        self.pub_offer.refresh_from_db()
        self.assertEqual(self.pub_offer.available_seats, 0)
        
        # Verify User 3 Accepted
        tp3.refresh_from_db()
        self.assertEqual(tp3.status_id.name, 'Aceptado')
        
        # Verify User 3 Chat Still Active
        chat3 = Chat.objects.get(id=chat_id3)
        self.assertTrue(chat3.is_active)

    def test_rejection_on_full_capacity(self):
         # Create interest (User 2 & User 3) for 1 seat
         self.pub_offer.available_seats = 1
         self.pub_offer.save()
         
         self.client.force_authenticate(user=self.user2)
         resp2 = self.client.post('/api/chat/interests/', {'publication_id': self.pub_offer.id})
         
         self.client.force_authenticate(user=self.user3)
         resp3 = self.client.post('/api/chat/interests/', {'publication_id': self.pub_offer.id})
         
         # Accept User 2
         self.client.force_authenticate(user=self.user1)
         self.client.post(f'/api/trips/trippassengers/{resp2.data['trip_passenger_id']}/accept/')
         
         # Verify User 3 Rejected (seats = 0)
         tp3 = TripPassenger.objects.get(id=resp3.data['trip_passenger_id'])
         self.assertEqual(tp3.status_id.name, 'Rechazado')
         
         # Verify User 3 Chat Closed
         chat3 = Chat.objects.get(id=resp3.data['chat_id'])
         self.assertFalse(chat3.is_active)

    def test_publication_inactive_closes_chats(self):
        # 1. Create interest (User 2)
        self.client.force_authenticate(user=self.user2)
        resp = self.client.post('/api/chat/interests/', {'publication_id': self.pub_offer.id})
        chat_id = resp.data['chat_id']
        tp_id = resp.data['trip_passenger_id']
        
        # 2. Accept User 2
        self.client.force_authenticate(user=self.user1)
        self.client.post(f'/api/trips/trippassengers/{tp_id}/accept/')
        
        # 3. Deactivate Publication
        self.pub_offer.is_active = False
        self.pub_offer.save()
        
        # 4. Verify Chat Closed
        chat = Chat.objects.get(id=chat_id)
        self.assertFalse(chat.is_active)

    def test_message_validation_on_status(self):
        # 1. Create interest (User 2)
        self.client.force_authenticate(user=self.user2)
        resp = self.client.post('/api/chat/interests/', {'publication_id': self.pub_offer.id})
        chat_id = resp.data['chat_id']
        tp_id = resp.data['trip_passenger_id']
        
        # 2. Send message (OK)
        resp_msg = self.client.post(f'/api/chat/chats/{chat_id}/messages/', {'content': 'Hi'})
        self.assertEqual(resp_msg.status_code, status.HTTP_201_CREATED)
        
        # 3. Accept User 2
        self.client.force_authenticate(user=self.user1)
        self.client.post(f'/api/trips/trippassengers/{tp_id}/accept/')
        
        # 4. Send message (Should Succeed now because Chat is Open for Accepted)
        self.client.force_authenticate(user=self.user2)
        resp_msg = self.client.post(f'/api/chat/chats/{chat_id}/messages/', {'content': 'Hi again'})
        self.assertEqual(resp_msg.status_code, status.HTTP_201_CREATED)
        
        # 5. Reject User 2 manually (simulate rejection)
        tp = TripPassenger.objects.get(id=tp_id)
        tp.status_id = TripPassengerStatus.objects.get(name='Rechazado')
        tp.save()
        
        # 6. Send message (Should Fail because Chat Closed on Rejection)
        resp_msg = self.client.post(f'/api/chat/chats/{chat_id}/messages/', {'content': 'Why rejected?'})
        self.assertEqual(resp_msg.status_code, status.HTTP_400_BAD_REQUEST)

    def test_finalize_trip_flow(self):
        # 1. Create interest (User 2)
        self.client.force_authenticate(user=self.user2)
        resp = self.client.post('/api/chat/interests/', {'publication_id': self.pub_offer.id})
        chat_id = resp.data['chat_id']
        tp_id = resp.data['trip_passenger_id']
        
        # 2. Accept User 2
        self.client.force_authenticate(user=self.user1)
        self.client.post(f'/api/trips/trippassengers/{tp_id}/accept/')
        
        # 3. Finalize Trip (Simulate driver finishing trip)
        trip = Trip.objects.get(publication_id=self.pub_offer.id)
        finalized_status, _ = TripStatus.objects.get_or_create(name='Finalizado')
        trip.status_id = finalized_status
        trip.finalized_at = timezone.now()
        trip.save()
        
        # 4. Verify Chat Closed
        chat = Chat.objects.get(id=chat_id)
        self.assertFalse(chat.is_active)
        
        # 5. Verify Message Blocked
        self.client.force_authenticate(user=self.user2)
        resp_msg = self.client.post(f'/api/chat/chats/{chat_id}/messages/', {'content': 'Bye'})
        self.assertEqual(resp_msg.status_code, status.HTTP_400_BAD_REQUEST)

    def test_trip_creation_populates_vehicle(self):
        # 1. User 2 shows interest in Offer
        self.client.force_authenticate(user=self.user2)
        resp = self.client.post('/api/chat/interests/', {'publication_id': self.pub_offer.id})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        
        # 2. Check Trip Vehicle
        trip = Trip.objects.get(publication_id=self.pub_offer.id)
        self.assertEqual(trip.vehicle_id, self.vehicle1)

    def test_trip_creation_request_no_vehicle(self):
        # 1. Create Request Publication by User 2
        pub_req = Publication.objects.create(
            user_id=self.user2,
            type_id=self.type_request,
            departure_place="Place C",
            destination="Place D",
            departure_datetime=timezone.now() + datetime.timedelta(days=1),
            lat_departure_place=1.0,
            lon_departure_place=1.0,
            lat_destination=2.0,
            lon_destination=2.0,
            available_seats=1,
            is_active=True
        )
        
        # 2. User 1 (Driver) shows interest
        self.client.force_authenticate(user=self.user1)
        resp = self.client.post('/api/chat/interests/', {'publication_id': pub_req.id})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        
        # 3. Check Trip Vehicle is None (default for now)
        trip = Trip.objects.get(publication_id=pub_req.id)
        self.assertIsNone(trip.vehicle_id)

    def test_finalize_passenger_flow(self):
        # 1. Create interest (User 2)
        self.client.force_authenticate(user=self.user2)
        resp = self.client.post('/api/chat/interests/', {'publication_id': self.pub_offer.id})
        chat_id = resp.data['chat_id']
        tp_id = resp.data['trip_passenger_id']
        
        # 2. Finalize Passenger (e.g. dropped off early or trip done)
        tp = TripPassenger.objects.get(id=tp_id)
        finalized_status, _ = TripPassengerStatus.objects.get_or_create(name='Finalizado')
        tp.status_id = finalized_status
        tp.finalized_at = timezone.now()
        tp.save()
        
        # 3. Verify Chat Closed
        chat = Chat.objects.get(id=chat_id)
        self.assertFalse(chat.is_active)
        
        # 4. Verify Message Blocked
        self.client.force_authenticate(user=self.user2)
        resp_msg = self.client.post(f'/api/chat/chats/{chat_id}/messages/', {'content': 'Bye'})
        self.assertEqual(resp_msg.status_code, status.HTTP_400_BAD_REQUEST)

