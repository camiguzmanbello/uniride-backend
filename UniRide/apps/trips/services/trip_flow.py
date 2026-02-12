from django.db import transaction
from django.db.models import F
from rest_framework.exceptions import ValidationError, APIException
from django.shortcuts import get_object_or_404
from django.utils import timezone
from apps.trips.models import Publication, Trip, TripPassenger, TripStatus, TripPassengerStatus
from apps.chat.models import Chat
from apps.users.models import User

def deactivate_expired_publications():
    """
    Busca todas las publicaciones activas cuya fecha de salida ya pasó
    y las desactiva, cerrando también sus solicitudes pendientes.
    """
    now = timezone.now()
    
    # Buscamos publicaciones que deberían estar inactivas
    expired_pubs = Publication.objects.filter(
        is_active=True,
        departure_datetime__lt=now
    )
    
    count = 0
    for pub in expired_pubs:
        pub.is_active = False
        pub.save() # Dispara signals para cerrar chats y pendientes
        count += 1
            
    return count

class ConflictError(APIException):
    """
    Excepción personalizada para conflictos de estado o recursos (HTTP 409).
    """
    status_code = 409
    default_detail = 'Conflict occurred.'
    default_code = 'conflict'

def user_has_active_trip(user: User) -> bool:
    """
    Verifica si el usuario tiene un viaje 'En curso' (Pendiente o En curso)
    ya sea como conductor o como pasajero aceptado.
    """
    # Como conductor
    if Trip.objects.filter(driver_id=user, status_id__name__in=['Pendiente', 'En curso']).exists():
        return True
    
    # Como pasajero aceptado
    if TripPassenger.objects.filter(passenger_id=user, status_id__name='Aceptado', trip_id__status_id__name__in=['Pendiente', 'En curso']).exists():
        return True
        
    return False

def create_interest(publication_id: int, passenger_user: User, seats_reserved: int = 1, driver_user: User = None) -> dict:
    """
    Maneja la lógica cuando un usuario muestra interés en una publicación (Oferta o Solicitud).
    
    Flujo:
    1. Verifica que la publicación esté activa.
    2. Determina quién es el conductor y quién el pasajero según el tipo de publicación.
    3. Verifica cupos disponibles (si es Oferta).
    4. Crea o recupera el Viaje (Trip).
    5. Crea o recupera la relación Pasajero-Viaje (TripPassenger).
    6. Crea o activa el Chat asociado.
    
    Retorna un diccionario con el TripPassenger, el Chat y el estado actual.
    """
    with transaction.atomic():
        # Bloquear la publicación para evitar condiciones de carrera en cupos concurrentes
        publication = Publication.objects.select_for_update().get(pk=publication_id)
        
        if not publication.is_active:
             raise ValidationError("La publicación no está activa.")
             
        pub_type = publication.type_id.name.lower()
        
        # Determinar roles de Conductor y Pasajero basados en el Tipo de Publicación
        if 'oferta' in pub_type:
            # En una oferta, el dueño de la publicación es el conductor
            driver = publication.user_id
            passenger = passenger_user
            
            # Verificación de lógica: El conductor no puede ser el pasajero de su propio viaje
            if driver.id == passenger.id:
                raise ValidationError("El conductor no puede ser pasajero.")
                
        elif 'solicitud' in pub_type:
            # En una solicitud, el interesado (driver_user) es el conductor
            if not driver_user:
                raise ValidationError("Se requiere un conductor para solicitudes.")
            driver = driver_user
            passenger = publication.user_id # El dueño de la solicitud es el pasajero
            
            if driver.id == passenger.id:
                raise ValidationError("El pasajero no puede ser conductor.")
        else:
             raise ValidationError(f"Tipo de publicación no soportado: {pub_type}")

        # Validar restricción de viaje único activo
        if user_has_active_trip(passenger):
             raise ValidationError("Ya tienes un viaje en curso. No puedes unirte a otro viaje hasta que finalice.")

        # Si el viaje no existe aún, validamos que el conductor no tenga otro viaje activo
        # Si ya existe, el conductor ya es parte de este viaje (se valida más abajo que sea el mismo conductor)
        if not hasattr(publication, 'trip'):
             if user_has_active_trip(driver):
                 raise ValidationError("El conductor ya tiene un viaje en curso y no puede iniciar otro.")

        # Validar cupos solo para Ofertas (las solicitudes no tienen cupos definidos igual)
        if 'oferta' in pub_type and publication.available_seats < seats_reserved:
             raise ConflictError("No hay suficientes asientos disponibles.")

        # Obtener instancias de Estados necesarios
        try:
            trip_status_pending = TripStatus.objects.get(name='Pendiente')
            tp_status_pending = TripPassengerStatus.objects.get(name='Pendiente')
        except (TripStatus.DoesNotExist, TripPassengerStatus.DoesNotExist):
            raise ValidationError("Estados de viaje no configurados en el sistema.")

        # Crear u Obtener Viaje (Trip)
        # Para Solicitudes, asegurar que no secuestramos un viaje existente con otro conductor
        trip = getattr(publication, 'trip', None)
        if trip:
            # Si ya existe un viaje para esta publicación, verificamos que sea el mismo conductor
            if trip.driver_id != driver:
                 raise ConflictError("Esta publicación ya tiene un viaje asociado con otro conductor.")
        else:
            # Determinar vehículo a usar
            vehicle = None
            if 'oferta' in pub_type:
                # Si es oferta, usamos el vehículo asociado a la publicación
                vehicle = publication.vehicle_id
            # Nota: Si es solicitud, vehicle queda None hasta que el conductor lo seleccione (mejora futura)
            
            trip = Trip.objects.create(
                publication_id=publication,
                driver_id=driver,
                status_id=trip_status_pending,
                vehicle_id=vehicle
            )

        # Crear u Obtener Pasajero del Viaje (TripPassenger)
        trip_passenger, created = TripPassenger.objects.get_or_create(
            trip_id=trip,
            passenger_id=passenger,
            defaults={
                'seats_reserved': seats_reserved,
                'status_id': tp_status_pending
            }
        )
        
        # Crear u Obtener Chat
        if hasattr(trip_passenger, 'chat'):
            # Si ya existe chat para este pasajero, asegurarse de que esté activo
            chat = trip_passenger.chat
            if not chat.is_active:
                chat.is_active = True
                chat.save()
        else:
            # Verificar si existe un chat previo por unique_together (consistencia de datos legados)
            existing_chat = Chat.objects.filter(publication=publication, passenger=passenger).first()
            if existing_chat:
                if existing_chat.trip_passenger != trip_passenger:
                     # Vincular el chat existente al nuevo TripPassenger si es necesario
                     existing_chat.trip_passenger = trip_passenger
                     existing_chat.save()
                chat = existing_chat
            else:
                # Crear nuevo chat
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
    Lógica para aceptar un pasajero en un viaje.
    
    Acciones:
    1. Verifica que el actor sea el conductor.
    2. Verifica cupos disponibles.
    3. Cambia estado del pasajero a 'Aceptado'.
    4. Descuenta cupos de la publicación.
    5. Si se acaban los cupos, rechaza automáticamente a los demás pendientes.
    """
    with transaction.atomic():
        try:
            # Bloqueamos el registro para evitar conflictos concurrentes
            # Usamos select_related para traer los datos relacionados en una sola consulta
            tp = TripPassenger.objects.select_for_update().select_related('trip_id', 'trip_id__publication_id', 'trip_id__publication_id__type_id').get(pk=trip_passenger_id)
        except TripPassenger.DoesNotExist:
            raise ValidationError("Pasajero no encontrado.")
            
        trip = tp.trip_id
        publication = trip.publication_id
        pub_type = publication.type_id.name.lower()
        
        # Validaciones de seguridad
        if trip.driver_id != actor_user:
            raise ValidationError("Solo el conductor puede aceptar pasajeros.")
            
        if tp.status_id.name != 'Pendiente':
            if tp.status_id.name == 'Aceptado':
                return tp # Idempotencia: si ya está aceptado, retornar sin error
            raise ValidationError(f"No se puede aceptar un pasajero en estado {tp.status_id.name}.")
            
        # Validar cupos
        # Si es oferta, validamos estrictamente los cupos disponibles
        if 'oferta' in pub_type and publication.available_seats < tp.seats_reserved:
            raise ConflictError("Cupos insuficientes.")
            
        # Actualizar Estado a Aceptado
        accepted_status = TripPassengerStatus.objects.get(name='Aceptado')
        tp.status_id = accepted_status
        tp.save()
        
        # Descontar cupos de la publicación de manera atómica
        if 'oferta' in pub_type:
            publication.available_seats = F('available_seats') - tp.seats_reserved
            publication.save()
            publication.refresh_from_db() # Recargar para obtener el valor actualizado
        else:
            # En Solicitud, al aceptar se considera completada.
            # Forzamos a 0 para indicar que ya no hay "demanda" pendiente y cerrar.
            publication.available_seats = 0
            publication.save()
        
        # Si se agotaron los cupos:
        # 1. Cambiar estado del viaje a "En curso"
        # 2. Rechazar a los demás pendientes
        if publication.available_seats == 0:
            # Actualizar estado del viaje a 'En curso'
            try:
                trip_status_in_progress = TripStatus.objects.get(name='En curso')
                trip.status_id = trip_status_in_progress
                trip.save()
            except TripStatus.DoesNotExist:
                # Si no existe el estado, logueamos o ignoramos, pero no rompemos el flujo crítico
                pass

            # Rechazar a otros pendientes
            rejected_status = TripPassengerStatus.objects.get(name='Rechazado')
            # Buscar otros pasajeros pendientes en este mismo viaje
            others = TripPassenger.objects.filter(trip_id=trip, status_id__name='Pendiente').exclude(id=tp.id)
            
            for other in others:
                other.status_id = rejected_status
                other.save() 
                # Nota: El cierre del chat para rechazados se maneja vía Signals (apps/trips/signals.py)
            
        return tp

def close_pending_for_publication(publication_id: int):
    """
    Cierra (cancela) todas las solicitudes pendientes de una publicación.
    Útil cuando una publicación se desactiva o cancela.
    """
    with transaction.atomic():
        try:
            publication = Publication.objects.get(pk=publication_id)
            if hasattr(publication, 'trip'):
                trip = publication.trip
                canceled_status = TripPassengerStatus.objects.get(name='Cancelado') # O usar Rechazado según regla de negocio
                
                passengers = TripPassenger.objects.filter(trip_id=trip, status_id__name='Pendiente')
                for p in passengers:
                    p.status_id = canceled_status
                    p.save()
                    # El cierre del chat se maneja automáticamente por Signals
        except Publication.DoesNotExist:
            pass
