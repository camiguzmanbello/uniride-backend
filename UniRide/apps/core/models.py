from django.db import models
from django.utils import timezone
from apps.users.models import User
from apps.trips.models import Publication

class PairingStatus(models.Model):
    name = models.CharField(max_length=50, unique=True)  # Ej: 'Pendiente', 'Aceptado', etc.

    def __str__(self):
        return self.name


class Pairing(models.Model):
    publication_id = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name='pairings')
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pairings')
    status_id = models.ForeignKey(PairingStatus, on_delete=models.PROTECT)
    time_response = models.PositiveIntegerField(null=True, blank=True, help_text="Tiempo (segundos) desde que recibió la notificación hasta que respondió")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=['status_id']),
            models.Index(fields=['publication_id', 'user_id']),
        ]
        unique_together = ('publication_id', 'user_id')
        verbose_name = 'Emparejamiento'
        verbose_name_plural = 'Emparejamientos'

    def __str__(self):
        return f"{self.user_id.name} en publicación #{self.publication_id.id} - Estado: {self.status_id.name}"

