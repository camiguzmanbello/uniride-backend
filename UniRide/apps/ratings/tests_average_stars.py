from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from apps.users.models import User, Role, VehicleType, Vehicle
from apps.trips.models import PublicationType, Publication, TripStatus, Trip
from apps.ratings.models import Rating
import datetime

class RatingsAverageStarsTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        role_driver, _ = Role.objects.get_or_create(name="Conductor")
        role_passenger, _ = Role.objects.get_or_create(name="Pasajero")
        self.driver = User.objects.create(email="driver@example.com", name="Driver", role_id=role_driver, is_active=True)
        self.user_a = User.objects.create(email="a@example.com", name="A", role_id=role_passenger, is_active=True)
        self.user_b = User.objects.create(email="b@example.com", name="B", role_id=role_passenger, is_active=True)
        vtype, _ = VehicleType.objects.get_or_create(name="Carro")
        vehicle = Vehicle.objects.create(user_id=self.driver, type_id=vtype, brand="Brand", plate="PLT-001", is_active=True)
        ptype, _ = PublicationType.objects.get_or_create(name="Oferta")
        status_pending, _ = TripStatus.objects.get_or_create(name="Pendiente")
        pub = Publication.objects.create(
            user_id=self.driver,
            type_id=ptype,
            vehicle_id=vehicle,
            departure_place="X",
            destination="Y",
            departure_datetime=timezone.now() + datetime.timedelta(days=1),
            lat_departure_place=0,
            lon_departure_place=0,
            lat_destination=0,
            lon_destination=0,
            available_seats=2,
            is_active=True
        )
        self.trip = Trip.objects.create(publication_id=pub, driver_id=self.driver, status_id=status_pending, vehicle_id=vehicle)

    def test_average_stars_with_ratings(self):
        Rating.objects.create(trip_id=self.trip, reviewer_id=self.user_a, reviewed_id=self.user_b, stars=4)
        Rating.objects.create(trip_id=self.trip, reviewer_id=self.driver, reviewed_id=self.user_b, stars=2)
        resp = self.client.get(f'/api/ratings/average-stars/{self.user_b.id}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertAlmostEqual(resp.data['average_stars'], 3.0)

    def test_average_stars_no_ratings(self):
        resp = self.client.get(f'/api/ratings/average-stars/{self.user_a.id}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['average_stars'], 0)
