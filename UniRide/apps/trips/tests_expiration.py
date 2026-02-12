from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from apps.users.models import User, Role, Vehicle, VehicleType
from apps.trips.models import Publication, PublicationType, TripStatus, TripPassengerStatus, Trip, TripPassenger
import datetime

class PublicationExpirationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Setup Roles and Users
        self.role = Role.objects.create(name="Estudiante")
        self.user1 = User.objects.create_user(
            username="user1",
            email="user1@test.com", 
            password="password123", 
            name="User One",
            role_id=self.role
        )
        self.user2 = User.objects.create_user(
            username="user2",
            email="user2@test.com", 
            password="password123", 
            name="User Two",
            role_id=self.role
        )
        
        # Setup Publication Types
        self.type_offer = PublicationType.objects.create(name="Oferta")
        self.type_request = PublicationType.objects.create(name="Solicitud")

        # Setup Trip Statuses
        self.status_pending, _ = TripStatus.objects.get_or_create(name='Pendiente')
        self.status_in_progress, _ = TripStatus.objects.get_or_create(name='En curso')
        
        self.tp_status_pending, _ = TripPassengerStatus.objects.get_or_create(name='Pendiente')
        self.tp_status_accepted, _ = TripPassengerStatus.objects.get_or_create(name='Aceptado')
        self.tp_status_rejected, _ = TripPassengerStatus.objects.get_or_create(name='Rechazado')
        self.tp_status_canceled, _ = TripPassengerStatus.objects.get_or_create(name='Cancelado')

        # Setup Vehicle for Offer
        self.v_type = VehicleType.objects.create(name="Carro")
        self.vehicle1 = Vehicle.objects.create(
            user_id=self.user1,
            type_id=self.v_type,
            brand="Toyota",
            plate="ABC-123",
            is_active=True
        )

    def test_deactivate_other_publications_on_trip_in_progress(self):
        # Escenario:
        # 1. Usuario 2 tiene una publicación de SOLICITUD activa.
        # 2. Usuario 1 tiene una publicación de OFERTA activa.
        # 3. Usuario 2 se une a la oferta de Usuario 1.
        # 4. Usuario 1 acepta a Usuario 2. El viaje pasa a 'En curso'.
        # 5. La solicitud de Usuario 2 debe desactivarse automáticamente.

        # 1. Pub de Usuario 2 (Solicitud)
        pub_user2 = Publication.objects.create(
            user_id=self.user2,
            type_id=self.type_request,
            departure_place="Home",
            destination="Uni",
            departure_datetime=timezone.now() + datetime.timedelta(days=1),
            lat_departure_place=1.0, lon_departure_place=1.0,
            lat_destination=2.0, lon_destination=2.0,
            available_seats=1,
            is_active=True
        )

        # 2. Pub de Usuario 1 (Oferta)
        pub_user1 = Publication.objects.create(
            user_id=self.user1,
            type_id=self.type_offer,
            vehicle_id=self.vehicle1,
            departure_place="Office",
            destination="Uni",
            departure_datetime=timezone.now() + datetime.timedelta(days=1),
            lat_departure_place=3.0, lon_departure_place=3.0,
            lat_destination=2.0, lon_destination=2.0,
            available_seats=1,
            is_active=True
        )

        # 3. Usuario 2 se une a la oferta
        self.client.force_authenticate(user=self.user2)
        resp_join = self.client.post('/api/chat/interests/', {'publication_id': pub_user1.id})
        self.assertEqual(resp_join.status_code, status.HTTP_201_CREATED)
        
        # Obtener el trip_passenger directamente de la base de datos
        from apps.trips.models import TripPassenger
        tp = TripPassenger.objects.filter(trip_id__publication_id=pub_user1.id, passenger_id=self.user2).first()
        self.assertIsNotNone(tp)
        tp_id = tp.id

        # 4. Usuario 1 acepta a Usuario 2
        self.client.force_authenticate(user=self.user1)
        resp_accept = self.client.post(f'/api/trips/trippassengers/{tp_id}/accept/')
        if resp_accept.status_code != status.HTTP_200_OK:
            print(f"DEBUG: Accept Error: {resp_accept.data}")
        self.assertEqual(resp_accept.status_code, status.HTTP_200_OK)

        # 5. Verificar que el viaje está 'En curso'
        trip = Trip.objects.get(publication_id=pub_user1.id)
        self.assertEqual(trip.status_id.name, 'En curso')

        # 6. VERIFICACIÓN CRÍTICA: La publicación de Usuario 2 debe estar INACTIVA
        pub_user2.refresh_from_db()
        self.assertFalse(pub_user2.is_active, "La publicación del pasajero debería haberse desactivado al iniciar el viaje.")
        
        # También la del conductor (aunque es la misma del viaje, se desactiva por la lógica general)
        pub_user1.refresh_from_db()
        self.assertFalse(pub_user1.is_active, "La publicación del conductor debería haberse desactivado al iniciar el viaje.")

    def test_manual_start_by_driver(self):
        # 1. Crear oferta con 2 cupos
        pub_offer = Publication.objects.create(
            user_id=self.user1,
            type_id=self.type_offer,
            vehicle_id=self.vehicle1,
            departure_place="A", destination="B",
            departure_datetime=timezone.now() + datetime.timedelta(days=1),
            lat_departure_place=0, lon_departure_place=0,
            lat_destination=0, lon_destination=0,
            available_seats=2,
            is_active=True
        )

        # 2. Usuario 2 se une y es aceptado
        self.client.force_authenticate(user=self.user2)
        self.client.post('/api/chat/interests/', {'publication_id': pub_offer.id})
        tp = TripPassenger.objects.get(trip_id__publication_id=pub_offer.id, passenger_id=self.user2)
        
        self.client.force_authenticate(user=self.user1)
        self.client.post(f'/api/trips/trippassengers/{tp.id}/accept/')
        
        # 3. Verificar estado inicial: El viaje sigue 'Pendiente' porque queda 1 cupo
        trip = Trip.objects.get(publication_id=pub_offer.id)
        self.assertEqual(trip.status_id.name, 'Pendiente')
        
        # 4. Verificar endpoint 'current' para el conductor (debe aparecer el viaje Pendiente)
        self.client.force_authenticate(user=self.user1)
        resp_current_driver = self.client.get('/api/trips/trips/current/')
        self.assertEqual(resp_current_driver.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_current_driver.data['id'], trip.id)

        # 5. Iniciar viaje manualmente
        resp_start = self.client.post(f'/api/trips/trips/{trip.id}/start/')
        self.assertEqual(resp_start.status_code, status.HTTP_200_OK)
        
        # 6. Verificar cambios
        trip.refresh_from_db()
        self.assertEqual(trip.status_id.name, 'En curso')
        
        pub_offer.refresh_from_db()
        self.assertFalse(pub_offer.is_active, "La publicación debería desactivarse al iniciar el viaje manualmente.")

    def test_get_trip_passengers(self):
        # 1. Crear viaje con un pasajero aceptado
        pub = Publication.objects.create(
            user_id=self.user1,
            type_id=self.type_offer,
            vehicle_id=self.vehicle1,
            departure_place="A", destination="B",
            departure_datetime=timezone.now() + datetime.timedelta(days=1),
            lat_departure_place=0, lon_departure_place=0,
            lat_destination=0, lon_destination=0,
            available_seats=2,
            is_active=True
        )
        trip = Trip.objects.create(
            publication_id=pub,
            driver_id=self.user1,
            status_id=self.status_pending,
            vehicle_id=self.vehicle1
        )
        TripPassenger.objects.create(
            trip_id=trip,
            passenger_id=self.user2,
            status_id=self.tp_status_accepted,
            seats_reserved=1
        )

        # 2. Consultar endpoint de pasajeros
        self.client.force_authenticate(user=self.user1)
        resp = self.client.get(f'/api/trips/trips/{trip.id}/passengers/')
        
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['passenger']['name'], self.user2.name)
        self.assertEqual(resp.data[0]['status'], 'Aceptado')

    def test_expired_publication_deactivation_on_list(self):
        # 1. Create a publication that is already "expired" manually in DB
        past_time = timezone.now() - datetime.timedelta(hours=2)
        pub = Publication.objects.create(
            user_id=self.user1,
            type_id=self.type_request,
            departure_place="Past Place",
            destination="Future Place",
            departure_datetime=past_time,
            lat_departure_place=1.0,
            lon_departure_place=1.0,
            lat_destination=2.0,
            lon_destination=2.0,
            available_seats=1,
            is_active=True
        )
        
        self.assertTrue(pub.is_active)
        
        # 2. Call the list endpoint
        resp = self.client.get('/api/trips/publications/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        
        # 3. Check if it was deactivated
        pub.refresh_from_db()
        self.assertFalse(pub.is_active)
        
        # 4. Check that it doesn't appear in the list (since we filtered by is_active=True in list)
        self.assertEqual(len(resp.data), 0)

    def test_cannot_create_publication_in_past(self):
        self.client.force_authenticate(user=self.user1)
        past_time = timezone.now() - datetime.timedelta(days=1)
        
        data = {
            'type_id': self.type_request.id,
            'departure_place': "Place A",
            'destination': "Place B",
            'departure_datetime': past_time,
            'lat_departure_place': 1.0,
            'lon_departure_place': 1.0,
            'lat_destination': 2.0,
            'lon_destination': 2.0,
            'available_seats': 1,
            'is_active': True
        }
        
        resp = self.client.post('/api/trips/publications/', data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("No puedes crear o activar una publicación con una fecha de viaje pasada.", str(resp.data))

    def test_future_publication_stays_active(self):
        future_time = timezone.now() + datetime.timedelta(days=1)
        pub = Publication.objects.create(
            user_id=self.user1,
            type_id=self.type_request,
            departure_place="Future Place",
            destination="Dest Place",
            departure_datetime=future_time,
            lat_departure_place=1.0,
            lon_departure_place=1.0,
            lat_destination=2.0,
            lon_destination=2.0,
            available_seats=1,
            is_active=True
        )
        
        resp = self.client.get('/api/trips/publications/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        
        pub.refresh_from_db()
        self.assertTrue(pub.is_active)
