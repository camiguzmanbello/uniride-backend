from django.db import models
from django.utils import timezone
from apps.users.models import User, Vehicle


class PublicationType(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Publication(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='publications')
    type_id = models.ForeignKey(PublicationType, on_delete=models.PROTECT)
    vehicle_id = models.ForeignKey(Vehicle, null=True, blank=True, on_delete=models.SET_NULL)
    departure_place = models.CharField(max_length=500)
    destination = models.CharField(max_length=500)
    departure_datetime = models.DateTimeField()
    lat_departure_place = models.FloatField()
    lon_departure_place = models.FloatField()
    lat_destination = models.FloatField()
    lon_destination = models.FloatField()
    available_seats = models.PositiveIntegerField(default=0)
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=['departure_datetime']),
            models.Index(fields=['destination']),
        ]

    def __str__(self):
        return f"{self.type_id.name} por {self.user_id.name} - {self.departure_datetime}"


class TripStatus(models.Model):
    name = models.CharField(max_length=50, unique=True)  # Ej: Pendiente, Aceptado, Finalizado, Cancelado

    def __str__(self):
        return self.name


class Trip(models.Model):
    publication_id = models.OneToOneField(Publication, on_delete=models.CASCADE, related_name='trip')
    driver_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='driven_trips')
    status_id = models.ForeignKey(TripStatus, on_delete=models.PROTECT)
    created_at = models.DateTimeField(default=timezone.now)
    finalized_at = models.DateTimeField(null=True, blank=True)
    cancel_reason = models.TextField(null=True, blank=True)
    auto_finalized = models.BooleanField(default=False)

    def __str__(self):
        return f"Viaje de {self.driver_id.name} - Estado: {self.status_id.name}"


class TripPassengerStatus(models.Model):
    name = models.CharField(max_length=50, unique=True)  # Ej: Aceptado, Cancelado, Finalizado

    def __str__(self):
        return self.name


class TripPassenger(models.Model):
    trip_id = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='passengers')
    passenger_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='joined_trips')
    seats_reserved = models.PositiveIntegerField(default=1)
    status_id = models.ForeignKey(TripPassengerStatus, on_delete=models.PROTECT)
    joined_at = models.DateTimeField(default=timezone.now)
    finalized_at = models.DateTimeField(null=True, blank=True)
    cancel_reason = models.TextField(null=True, blank=True)
    auto_finalized = models.BooleanField(default=False)

    class Meta:
        unique_together = ('trip_id', 'passenger_id')

    def __str__(self):
        return f"{self.passenger_id.name} en {self.trip}"
