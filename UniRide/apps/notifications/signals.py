from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.chat.models import Message
from apps.notifications.services.push import notify_user_push
from apps.notifications.models import Notification

@receiver(post_save, sender=Message)
def new_chat_message(sender, instance, created, **kwargs):
    if created:
        chat = instance.chat_id
        if not chat.is_active:
            return
        if instance.sender_id == chat.driver:
            recipient = chat.passenger
        else:
            recipient = chat.driver
        metadata = {
            'chat_id': chat.id,
            'message_id': instance.id,
            'sender_id': instance.sender_id.id,
            'sender_name': instance.sender_id.name
        }
        if chat.trip_passenger and chat.trip_passenger.trip_id:
            metadata['trip_id'] = chat.trip_passenger.trip_id.id
        notification = Notification.objects.create(
            recipient=recipient,
            type='NEW_CHAT_MESSAGE',
            title='Nuevo Mensaje',
            message=instance.content,
            metadata=metadata
        )
        notify_user_push(
            user=recipient,
            title=notification.title,
            body=notification.message,
            data=notification.metadata
        )
