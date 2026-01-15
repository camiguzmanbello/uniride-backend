from django.db import transaction
from django.db.models import F
from rest_framework.exceptions import ValidationError, APIException
from django.shortcuts import get_object_or_404
from apps.trips.models import Publication, Trip, TripPassenger, TripStatus, TripPassengerStatus
from apps.chat.models import Chat
from apps.users.models import User

class ConflictError(APIException):
    status_code = 409
    default_detail = 'Conflict occurred.'
    default_code = 'conflict'

def create_interest(publication_id: int, passenger_user: User, seats_reserved: int = 1, driver_user: User = None) -> dict:
    """
    Crea Trip (si no existe), TripPassenger y Chat.
    Maneja lógica para Ofertas y Solicitudes.
    """
    with transaction.atomic():
        # Lock publication to check consistency
        publication = Publication.objects.select_for_update().get(pk=publication_id)
        
        if not publication.is_active:
             raise ValidationError("La publicación no está activa.")
             
        pub_type = publication.type_id.name.lower()
        
        # Determine Driver and Passenger roles based on Publication Type
        if 'oferta' in pub_type:
            driver = publication.user_id
            passenger = passenger_user
            # Sanity check: Driver cannot be passenger
            if driver.id == passenger.id:
                raise ValidationError("El conductor no puede ser pasajero.")
        elif 'solicitud' in pub_type:
            if not driver_user:
                raise ValidationError("Se requiere un conductor para solicitudes.")
            driver = driver_user
            passenger = publication.user_id
            
            if driver.id == passenger.id:
                raise ValidationError("El pasajero no puede ser conductor.")
        else:
             raise ValidationError(f"Tipo de publicación no soportado: {pub_type}")

        if 'oferta' in pub_type and publication.available_seats < seats_reserved:
             raise ConflictError("No hay suficientes asientos disponibles.")

        # Get Statuses
        try:
            trip_status_pending = TripStatus.objects.get(name='Pendiente')
            tp_status_pending = TripPassengerStatus.objects.get(name='Pendiente')
        except (TripStatus.DoesNotExist, TripPassengerStatus.DoesNotExist):
            raise ValidationError("Estados de viaje no configurados en el sistema.")

        # Create/Get Trip
        # For Solicitud, ensure we don't hijack an existing trip with different driver
        trip = getattr(publication, 'trip', None)
        if trip:
            if trip.driver_id != driver:
                 raise ConflictError("Esta publicación ya tiene un viaje asociado con otro conductor.")
        else:
            trip = Trip.objects.create(
                publication_id=publication,
                driver_id=driver,
                status_id=trip_status_pending
            )

        # Create/Get TripPassenger
        trip_passenger, created = TripPassenger.objects.get_or_create(
            trip_id=trip,
            passenger_id=passenger,
            defaults={
                'seats_reserved': seats_reserved,
                'status_id': tp_status_pending
            }
        )
        
        # Create/Get Chat
        if hasattr(trip_passenger, 'chat'):
            chat = trip_passenger.chat
            if not chat.is_active:
                chat.is_active = True
                chat.save()
        else:
            # Check if Chat exists by unique_together (legacy/migration consistency)
            # If Chat(pub, passenger) exists but not linked to this trip_passenger (shouldn't happen if OneToOne is correct)
            # But OneToOne is Chat->TripPassenger.
            # If Chat exists, it might not be linked?
            # If we just migrated, it SHOULD be linked.
            # But if unique_together triggers?
            existing_chat = Chat.objects.filter(publication=publication, passenger=passenger).first()
            if existing_chat:
                if existing_chat.trip_passenger != trip_passenger:
                     # Link it?
                     existing_chat.trip_passenger = trip_passenger
                     existing_chat.save()
                chat = existing_chat
            else:
                chat = Chat.objects.create(
                    trip_passenger=trip_passenger,
                    publication=publication,
                    driver=driver,
                    passenger=passenger
                )
            
        return {
            "trip_passenger": trip_passenger,
            "chat": chat,
            "status": trip_passenger.status_id.name
        }

def accept_passenger(trip_passenger_id: int, actor_user: User):
    """
    Acepta un pasajero, actualiza cupos y rechaza a los demás si no hay cupos.
    """
    with transaction.atomic():
        try:
            # Fix select_related names to match model fields (trip_id, trip_id__publication_id)
            tp = TripPassenger.objects.select_for_update().select_related('trip_id', 'trip_id__publication_id').get(pk=trip_passenger_id)
        except TripPassenger.DoesNotExist:
            raise ValidationError("Pasajero no encontrado.")
            
        trip = tp.trip_id
        publication = trip.publication_id
        
        if trip.driver_id != actor_user:
            raise ValidationError("Solo el conductor puede aceptar pasajeros.")
            
        if tp.status_id.name != 'Pendiente':
            if tp.status_id.name == 'Aceptado':
                return tp
            raise ValidationError(f"No se puede aceptar un pasajero en estado {tp.status_id.name}.")
            
        if publication.available_seats < tp.seats_reserved:
            raise ConflictError("Cupos insuficientes.")
            
        # Update Status
        accepted_status = TripPassengerStatus.objects.get(name='Aceptado')
        tp.status_id = accepted_status
        tp.save()
        
        
        
        publication.available_seats = F('available_seats') - tp.seats_reserved
        publication.save()
        publication.refresh_from_db() # Get the new value
        
        if publication.available_seats == 0:
            # Reject others
            rejected_status = TripPassengerStatus.objects.get(name='Rechazado')
            others = TripPassenger.objects.filter(trip_id=trip, status_id__name='Pendiente').exclude(id=tp.id)
            
            for other in others:
                other.status_id = rejected_status
                other.save() 
                # Chat closing handled by signal
            
        return tp

def close_pending_for_publication(publication_id: int):
    with transaction.atomic():
        try:
            publication = Publication.objects.get(pk=publication_id)
            if hasattr(publication, 'trip'):
                trip = publication.trip
                canceled_status = TripPassengerStatus.objects.get(name='Cancelado') # or Rechazado
                
                passengers = TripPassenger.objects.filter(trip_id=trip, status_id__name='Pendiente')
                for p in passengers:
                    p.status_id = canceled_status
                    p.save()
                    # Chat closing handled by signal
        except Publication.DoesNotExist:
            pass
