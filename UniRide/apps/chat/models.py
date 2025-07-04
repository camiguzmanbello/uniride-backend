from django.db import models
from django.utils import timezone
from apps.users.models import User
from apps.trips.models import Publication


class Chat(models.Model):
    publication_id = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name='chats')
    passenger_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chats_as_passenger')
    driver_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chats_as_driver')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('publication_id', 'passenger_id')
        indexes = [
            models.Index(fields=['is_active']),
        ]
        verbose_name = 'Chat'
        verbose_name_plural = 'Chats'

    def __str__(self):
        return f"Chat entre {self.passenger_id.name} y {self.driver_id.name} (Pub ID: {self.publication_id.id})"


class Message(models.Model):
    chat_id = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    sender_id = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    is_quick_message = models.BooleanField(default=False)
    sent_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=['sent_at']),
        ]
        verbose_name = 'Mensaje'
        verbose_name_plural = 'Mensajes'

    def __str__(self):
        return f"Mensaje de {self.sender_id.name} en chat {self.chat_id.id}"

