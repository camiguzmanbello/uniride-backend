from django.db import models

# Create your models here.
from django.db import models

# matching/models.py
from django.db import models

class Route(models.Model):
    """
    Ruta lógica del sistema.
    No es visible para el usuario.
    Se usa solo para clasificar coordenadas.
    """
    name = models.CharField(max_length=100)
    direction = models.CharField(
        max_length=20,
        choices=[
            ('MUNI_TO_U', 'Municipio → Universidad'),
            ('U_TO_MUNI', 'Universidad → Municipio'),
        ]
    )

    def __str__(self):
        return self.name

class RoutePoint(models.Model):
    """
    Puntos virtuales de una ruta.
    Sirven para aproximar cercanía.
    """
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='points')
    name = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ['order']

class PublicationRoute(models.Model):
    """
    Relación interna entre una publicación y una ruta.
    NO modifica la tabla Publication.
    """
    publication = models.OneToOneField(
        'trips.Publication',
        on_delete=models.CASCADE,
        related_name='route_info'
    )
    route = models.ForeignKey(Route, on_delete=models.PROTECT)
    closest_point = models.ForeignKey(RoutePoint, on_delete=models.PROTECT)

class MatchSuggestion(models.Model):
    """
    Sugerencia de pasajero para un conductor.
    Solo el conductor la ve.
    """
    driver_publication = models.ForeignKey(
        'trips.Publication',
        on_delete=models.CASCADE,
        related_name='suggestions'
    )
    passenger_publication = models.ForeignKey(
        'trips.Publication',
        on_delete=models.CASCADE
    )

    score = models.FloatField()
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('driver_publication', 'passenger_publication')
