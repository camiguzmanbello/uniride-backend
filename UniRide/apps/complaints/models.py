from django.db import models
from django.utils import timezone
from apps.users.models import User
from apps.trips.models import Trip


class ComplaintType(models.Model):
    name = models.CharField(max_length=100, unique=True)  # Ej: Técnica, Comportamiento, Otro
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name
    
class ComplaintStatus(models.Model):
    name = models.CharField(max_length=50, unique=True)  # Ej: 'Pendiente', 'Resuelta', 'Rechazada'

    def __str__(self):
        return self.name

class Complaint(models.Model):
    reporter_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaints_made')
    reported_user_id = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='complaints_received')
    type_id = models.ForeignKey(ComplaintType, on_delete=models.PROTECT)
    trip_id = models.ForeignKey(Trip, null=True, blank=True, on_delete=models.SET_NULL)
    description = models.TextField()
    status_id = models.ForeignKey(ComplaintStatus, on_delete=models.PROTECT)
    created_at = models.DateTimeField(default=timezone.now)
    resolved_at = models.DateTimeField(null=True, blank=True)
    admin_id = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='complaints_resolved')

    class Meta:
        indexes = [
            models.Index(fields=['status_id']),
            models.Index(fields=['type_id']),
        ]
        verbose_name = 'Queja'
        verbose_name_plural = 'Quejas'

    def __str__(self):
        return f"Queja de {self.reporter_id.name} - Tipo: {self.type_id.name} - Estado: {self.status_id.name}"
