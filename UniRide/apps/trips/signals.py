from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.trips.models import Publication, TripPassenger, Trip
from apps.trips.services.trip_flow import close_pending_for_publication

@receiver(post_save, sender=Publication)
def publication_changed(sender, instance, created, **kwargs):
    if not created and not instance.is_active:
        close_pending_for_publication(instance.id)
        
        # Cerrar todos los chats asociados a esta publicación (incluso aceptados)
        from apps.chat.models import Chat
        from django.utils import timezone
        chats = Chat.objects.filter(publication=instance, is_active=True)
        for chat in chats:
            chat.is_active = False
            chat.closed_at = timezone.now()
            chat.save()

@receiver(post_save, sender=Trip)
def trip_changed(sender, instance, created, **kwargs):
    # 1. Cuando Trip.status pase a 'En curso':
    # Desactivar publicaciones activas del conductor y pasajeros aceptados.
    if not created and instance.status_id.name == 'En curso':
        # Desactivar publicaciones del conductor
        Publication.objects.filter(user_id=instance.driver_id, is_active=True).update(is_active=False)
        
        # Desactivar publicaciones de los pasajeros aceptados
        passenger_ids = instance.passengers.filter(status_id__name='Aceptado').values_list('passenger_id', flat=True)
        Publication.objects.filter(user_id__in=passenger_ids, is_active=True).update(is_active=False)

    # 2. Cuando Trip.status pase a Finalizado o Cancelado:
    # Cerrar todos los chats asociados a ese viaje.
    if not created and instance.status_id.name in ['Finalizado', 'Cancelado']:
        from apps.chat.models import Chat
        # Obtener todos los TripPassenger de este Trip
        passengers = instance.passengers.all()
        for passenger in passengers:
            if hasattr(passenger, 'chat'):
                chat = passenger.chat
                if chat.is_active:
                    chat.is_active = False
                    chat.closed_at = instance.finalized_at
                    if not chat.closed_at:
                        from django.utils import timezone
                        chat.closed_at = timezone.now()
                    chat.save()

@receiver(post_save, sender=TripPassenger)
def trip_passenger_changed(sender, instance, created, **kwargs):
    # "El chat solo debe cerrarse si el TripPassenger pasa a "Rechazado", "Cancelado" 
    # o si la publicación o el viaje se desactivan/finalizan."
    # Aceptado -> Chat sigue abierto.
    # Pendiente -> Chat sigue abierto.
    # Se agrega "Finalizado" a la lista de cierre.
    if instance.status_id.name in ['Rechazado', 'Cancelado', 'Finalizado']:
        if hasattr(instance, 'chat'):
            chat = instance.chat
            if chat.is_active:
                chat.is_active = False
                chat.closed_at = instance.finalized_at
                if not chat.closed_at:
                    from django.utils import timezone
                    chat.closed_at = timezone.now()
                chat.save()
