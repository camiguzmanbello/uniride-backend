from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from apps.users.models import User, Role, Vehicle, VehicleType
from apps.trips.models import Publication, PublicationType, Trip, TripPassenger, TripStatus, TripPassengerStatus
import datetime

class RestrictionsTestCase(TestCase):
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
        
        # Create Statuses
        self.status_pending, _ = TripStatus.objects.get_or_create(name='Pendiente')
        self.status_in_progress, _ = TripStatus.objects.get_or_create(name='En curso')
        self.status_finalized, _ = TripStatus.objects.get_or_create(name='Finalizado')
        
        self.tp_status_pending, _ = TripPassengerStatus.objects.get_or_create(name='Pendiente')
        self.tp_status_accepted, _ = TripPassengerStatus.objects.get_or_create(name='Aceptado')
        self.tp_status_rejected, _ = TripPassengerStatus.objects.get_or_create(name='Rechazado')
        self.tp_status_canceled, _ = TripPassengerStatus.objects.get_or_create(name='Cancelado')

    def test_max_one_active_publication(self):
        self.client.force_authenticate(user=self.user1)
        
        # 1. Create first publication (Active)
        data = {
            'type_id': self.type_offer.id,
            'vehicle_id': self.vehicle1.id,
            'departure_place': "Place A",
            'destination': "Place B",
            'departure_datetime': timezone.now() + datetime.timedelta(days=1),
            'lat_departure_place': 1.0,
            'lon_departure_place': 1.0,
            'lat_destination': 2.0,
            'lon_destination': 2.0,
            'available_seats': 1,
            'is_active': True
        }
        resp1 = self.client.post('/api/trips/publications/', data)
        self.assertEqual(resp1.status_code, status.HTTP_201_CREATED)
        
        # 2. Try to create second publication (Active) -> Should Fail
        resp2 = self.client.post('/api/trips/publications/', data)
        self.assertEqual(resp2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Ya tienes una publicación activa. Debes finalizarla o cancelarla antes de crear una nueva.", str(resp2.data))
        
        # 3. Deactivate first publication
        pub1 = Publication.objects.get(id=resp1.data['id'])
        pub1.is_active = False
        pub1.save()
        
        # 4. Try to create second publication (Active) -> Should Succeed
        resp3 = self.client.post('/api/trips/publications/', data)
        self.assertEqual(resp3.status_code, status.HTTP_201_CREATED)

    def test_cannot_create_publication_if_in_active_trip(self):
        # User 1 has an active trip (as driver)
        pub = Publication.objects.create(
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
            is_active=False # Inactive publication, but Trip is active
        )
        trip = Trip.objects.create(
            publication_id=pub,
            driver_id=self.user1,
            status_id=self.status_pending, # Active Trip
            vehicle_id=self.vehicle1
        )
        
        self.client.force_authenticate(user=self.user1)
        
        # Try to create active publication
        data = {
            'type_id': self.type_offer.id,
            'vehicle_id': self.vehicle1.id,
            'departure_place': "Place C",
            'destination': "Place D",
            'departure_datetime': timezone.now() + datetime.timedelta(days=1),
            'lat_departure_place': 1.0,
            'lon_departure_place': 1.0,
            'lat_destination': 2.0,
            'lon_destination': 2.0,
            'available_seats': 1,
            'is_active': True
        }
        resp = self.client.post('/api/trips/publications/', data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Ya tienes un viaje en curso. No puedes crear una publicación hasta que finalice.", str(resp.data))

    def test_cannot_join_trip_if_in_active_trip(self):
        # Setup: User 1 has offer. User 2 joins and is ACCEPTED.
        # User 2 tries to join another trip (User 3's offer).
        
        # Offer 1 (User 1)
        pub1 = Publication.objects.create(
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
        
        # Offer 2 (User 3)
        pub2 = Publication.objects.create(
            user_id=self.user3,
            type_id=self.type_offer,
            # vehicle missing but irrelevant for test
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

        # User 2 joins Offer 1
        self.client.force_authenticate(user=self.user2)
        resp = self.client.post('/api/chat/interests/', {'publication_id': pub1.id})
        tp_id = resp.data['trip_passenger_id']
        
        # User 1 accepts User 2 -> User 2 is now in ACTIVE trip
        self.client.force_authenticate(user=self.user1)
        resp_accept = self.client.post(f'/api/trips/trippassengers/{tp_id}/accept/')
        self.assertEqual(resp_accept.status_code, status.HTTP_200_OK, resp_accept.data)
        
        # User 2 tries to join Offer 2
        self.client.force_authenticate(user=self.user2)
        resp2 = self.client.post('/api/chat/interests/', {'publication_id': pub2.id})
        
        self.assertEqual(resp2.status_code, status.HTTP_400_BAD_REQUEST)
        # Check validation error message (it might be in list or string)
        self.assertTrue("Ya tienes un viaje en curso. No puedes unirte a otro viaje hasta que finalice." in str(resp2.data))

