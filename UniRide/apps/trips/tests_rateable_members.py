from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from apps.users.models import User, Role, Vehicle, VehicleType
from apps.trips.models import Publication, PublicationType, Trip, TripPassenger, TripStatus, TripPassengerStatus
import datetime

class RateableMembersTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.role_driver, _ = Role.objects.get_or_create(name="Conductor")
        self.role_passenger, _ = Role.objects.get_or_create(name="Pasajero")
        self.user1 = User.objects.create(email="driver@example.com", name="Driver", role_id=self.role_driver, is_active=True)
        self.user2 = User.objects.create(email="p1@example.com", name="Passenger1", role_id=self.role_passenger, is_active=True)
        self.user3 = User.objects.create(email="p2@example.com", name="Passenger2", role_id=self.role_passenger, is_active=True)
        self.type_offer, _ = PublicationType.objects.get_or_create(name="Oferta")
        self.v_type, _ = VehicleType.objects.get_or_create(name="Carro")
        self.vehicle1 = Vehicle.objects.create(user_id=self.user1, type_id=self.v_type, brand="Toyota", plate="XYZ-987", is_active=True)
        self.status_pending, _ = TripStatus.objects.get_or_create(name="Pendiente")
        self.tp_status_accepted, _ = TripPassengerStatus.objects.get_or_create(name="Aceptado")
        pub = Publication.objects.create(
            user_id=self.user1,
            type_id=self.type_offer,
            vehicle_id=self.vehicle1,
            departure_place="A",
            destination="B",
            departure_datetime=timezone.now() + datetime.timedelta(days=1),
            lat_departure_place=0,
            lon_departure_place=0,
            lat_destination=0,
            lon_destination=0,
            available_seats=3,
            is_active=True
        )
        self.trip = Trip.objects.create(
            publication_id=pub,
            driver_id=self.user1,
            status_id=self.status_pending,
            vehicle_id=self.vehicle1
        )
        TripPassenger.objects.create(
            trip_id=self.trip,
            passenger_id=self.user2,
            status_id=self.tp_status_accepted,
            seats_reserved=1
        )
        TripPassenger.objects.create(
            trip_id=self.trip,
            passenger_id=self.user3,
            status_id=self.tp_status_accepted,
            seats_reserved=1
        )

    def test_rateable_members_for_passenger(self):
        self.client.force_authenticate(user=self.user2)
        resp = self.client.get(f'/api/trips/trips/{self.trip.id}/rateable_members/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        members = resp.data['members']
        self.assertEqual(len(members), 2)
        names = {m['name'] for m in members}
        self.assertIn(self.user1.name, names)
        self.assertIn(self.user3.name, names)

    def test_rateable_members_for_driver(self):
        self.client.force_authenticate(user=self.user1)
        resp = self.client.get(f'/api/trips/trips/{self.trip.id}/rateable_members/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        members = resp.data['members']
        self.assertEqual(len(members), 2)
        names = {m['name'] for m in members}
        self.assertIn(self.user2.name, names)
        self.assertIn(self.user3.name, names)
