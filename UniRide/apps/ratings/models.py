from django.db import models
from django.utils import timezone
from apps.users.models import User
from apps.trips.models import Trip


class Rating(models.Model):
    trip_id = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='ratings')
    reviewer_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_ratings')
    reviewed_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_ratings')
    stars = models.PositiveSmallIntegerField()  # de 1 a 5
    comment = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('trip_id', 'reviewer_id', 'reviewed_id')
        indexes = [
            models.Index(fields=['reviewed_id']),
            models.Index(fields=['trip_id']),
        ]
        verbose_name = 'Calificación'
        verbose_name_plural = 'Calificaciones'

    def __str__(self):
        return f"{self.reviewer_id.name} calificó a {self.reviewed_id.name} con {self.stars} estrellas"

