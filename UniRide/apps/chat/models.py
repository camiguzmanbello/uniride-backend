from django.db import models
from django.utils import timezone
from apps.users.models import User
from apps.trips.models import Publication


class Chat(models.Model):
    # Referencia opcional a la publicación origen.
    # Puede ser una oferta (type_id==2) o una solicitud (type_id==1)
    publication = models.ForeignKey(
        Publication,
        on_delete=models.CASCADE,
        related_name='chats'
    )

    passenger = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chats_as_passenger'
    )
    driver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chats_as_driver'
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    closed_at = models.DateTimeField(null=True, blank=True)
    
    trip_passenger = models.OneToOneField(
        'trips.TripPassenger',
        on_delete=models.CASCADE,
        related_name='chat',
        null=True,
        blank=True
    )

    class Meta:
        # Un pasajero sólo puede tener un chat por publicación
        unique_together = ('publication', 'passenger')
        indexes = [
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"Chat: pub={self.publication_id} passenger={self.passenger_id} driver={self.driver_id}"

class Message(models.Model):
    chat_id = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    sender_id = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    is_quick_message = models.BooleanField(default=False)
    sent_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)


    class Meta:
        indexes = [
            models.Index(fields=['sent_at']),
        ]
        verbose_name = 'Mensaje'
        verbose_name_plural = 'Mensajes'

    def __str__(self):
        return f"Mensaje de {self.sender_id.name} en chat {self.chat_id.id}"

