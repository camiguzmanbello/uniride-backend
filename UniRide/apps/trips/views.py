from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, serializers
from .serializers import *
from rest_framework.viewsets import ModelViewSet
from django.db.models import Q
from rest_framework.decorators import action
from apps.trips.services.trip_flow import (
    accept_passenger, 
    close_pending_for_publication,
    deactivate_expired_publications
)
from apps.chat.models import Chat
from django.utils import timezone
from apps.match.services.route_service import assign_route_to_publication

class PublicationTypeViewSet(ModelViewSet):

    permission_classes = [permissions.AllowAny]

    queryset = PublicationType.objects.all()
    serializer_class = PublicationTypeSerializer


class PublicationViewSet(ModelViewSet):

    permission_classes = [permissions.AllowAny]

    serializer_class = PublicationSerializer

    def get_queryset(self):
        # Desactivar publicaciones vencidas de forma perezosa
        deactivate_expired_publications()
        
        # Por defecto, en el listado general solo mostramos las activas
        # Si es un detalle (retrieve) o una acción específica, DRF usará el ID
        # pero para el listado filtramos por is_active=True
        queryset = Publication.objects.all()
        
        # Opcional: Si queremos que el listado general (/api/trips/publications/) 
        # solo devuelva las activas por defecto:
        if self.action == 'list':
            queryset = queryset.filter(is_active=True)
            
        return queryset

    #para que al crear una publicacion se asigne el user logueado
    def perform_create(self, serializer):
        publication = serializer.save(user_id=self.request.user)

        # asigna ruta y crea route_info correctamente
        assign_route_to_publication(publication)


    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated], serializer_class=serializers.Serializer)
    def deactivate(self, request, pk=None):
        """
        Endpoint para que el propietario desactive su publicación.
        Esto también cerrará (cancelará) las solicitudes pendientes asociadas.
        """
        publication = self.get_object()
        
        # Validar que sea el propietario
        if publication.user_id != request.user:
            return Response({"detail": "Solo el propietario puede desactivar la publicación."}, status=status.HTTP_403_FORBIDDEN)
            
        if not publication.is_active:
            return Response({"detail": "La publicación ya está inactiva."}, status=status.HTTP_400_BAD_REQUEST)
            
        # Desactivar
        publication.is_active = False
        publication.save()
        
        # Cerrar pendientes (limpieza)
        close_pending_for_publication(publication.id)
        
        return Response(PublicationSerializer(publication).data)
    

class TripPassengerViewSet(ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TripPassengerSerializer
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return TripPassenger.objects.none()
        return TripPassenger.objects.filter(
            Q(passenger_id=user) | Q(trip_id__driver_id=user)
        )

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        try:
            tp = accept_passenger(pk, request.user)
            return Response(TripPassengerSerializer(tp).data)
        except Exception as e:
            status_code = status.HTTP_400_BAD_REQUEST
            detail = str(e)
            if hasattr(e, 'status_code'):
                status_code = e.status_code
            if hasattr(e, 'detail'):
                detail = e.detail
            return Response({"detail": detail}, status=status_code)

class TripStatusViewSet(ModelViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = TripStatus.objects.all()
    serializer_class = TripStatusSerializer


class TripPassengerStatusViewSet(ModelViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = TripPassengerStatus.objects.all()
    serializer_class = TripPassengerStatusSerializer

class TripViewSet(ModelViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = Trip.objects.all()
    serializer_class = TripSerializer

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def history(self, request):
        """
        Retorna el historial de viajes del usuario (como conductor o pasajero).
        Ordenado por fecha de partida (descendente).
        Excluye los viajes activos (Pendiente/En curso) donde el usuario participa activamente,
        para evitar duplicidad con el endpoint 'current'.
        """
        user = request.user
        
        driven_trips = Trip.objects.filter(driver_id=user).exclude(
            status_id__name__in=['Pendiente', 'En curso', 'Pendiente finalizado']
        )
        
        joined_trips = Trip.objects.filter(passengers__passenger_id=user).filter(
            Q(status_id__name__in=['Finalizado', 'Cancelado']) |
            Q(passengers__status_id__name__in=['Rechazado', 'Cancelado'])
        )
        
        # Unir y ordenar
        # Usamos distinct() para evitar duplicados si la lógica permitiera unirse múltiples veces (raro pero posible)
        history_trips = (driven_trips | joined_trips).distinct().select_related(
            'publication_id', 'driver_id', 'status_id'
        ).order_by('-publication_id__departure_datetime')
        
        page = self.paginate_queryset(history_trips)
        if page is not None:
            serializer = TripHistorySerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
            
        serializer = TripHistorySerializer(history_trips, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def current(self, request):
        """
        Retorna el viaje actual (Activo) del usuario.
        Considera:
        - Para conductores: Viajes 'Pendiente', 'En curso' o 'Pendiente Cancelación'.
        - Para pasajeros: Viajes 'En curso' o 'Pendiente Cancelación' (si están aceptados),
          o viajes 'Pendiente' SI ya han sido aceptados por el conductor.
        Retorna 204 No Content si no tiene viaje activo.
        """
        user = request.user
        
        active_statuses_driver = ['Pendiente', 'En curso', 'Pendiente Cancelación', 'Pendiente finalizado']
        active_driven = Trip.objects.filter(
            driver_id=user,
            status_id__name__in=active_statuses_driver
        ).first()
        
        if active_driven:
            serializer = TripHistorySerializer(active_driven, context={'request': request})
            return Response(serializer.data)
            
        active_joined = Trip.objects.filter(
            passengers__passenger_id=user,
            passengers__status_id__name='Aceptado'
        ).filter(
            Q(status_id__name__in=['Pendiente', 'En curso', 'Pendiente Cancelación', 'Pendiente finalizado'])
        ).first()
        
        if not active_joined:
            active_joined = Trip.objects.filter(
                passengers__passenger_id=user,
                passengers__status_id__name='Finalizado',
                status_id__name__in=['En curso', 'Pendiente Cancelación', 'Pendiente finalizado']
            ).first()

        if active_joined:
            serializer = TripHistorySerializer(active_joined, context={'request': request})
            return Response(serializer.data)
            
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def start(self, request, pk=None):
        """
        Permite al conductor iniciar el viaje de manera manual, incluso si no se han llenado los cupos.
        Cambia el estado del viaje a 'En curso'.
        """
        trip = self.get_object()
        user = request.user
        
        # Validar que sea el conductor
        if trip.driver_id != user:
            return Response({"detail": "Solo el conductor puede iniciar el viaje."}, status=status.HTTP_403_FORBIDDEN)
            
        # Validar estado actual
        if trip.status_id.name != 'Pendiente':
            return Response({"detail": f"No se puede iniciar un viaje en estado {trip.status_id.name}."}, status=status.HTTP_400_BAD_REQUEST)
            
        # Validar que haya al menos un pasajero aceptado
        if not trip.passengers.filter(status_id__name='Aceptado').exists():
            return Response({"detail": "No puedes iniciar el viaje sin al menos un pasajero aceptado."}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            in_progress_status = TripStatus.objects.get(name='En curso')
            rejected_status = TripPassengerStatus.objects.get(name='Rechazado')
        except (TripStatus.DoesNotExist, TripPassengerStatus.DoesNotExist):
            return Response({"detail": "Error de configuración: Estados necesarios no encontrados."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        # 1. Cambiar estado del viaje
        trip.status_id = in_progress_status
        trip.save()
        
        # 2. Rechazar a los demás pendientes que no fueron aceptados antes de iniciar
        pending_passengers = trip.passengers.filter(status_id__name='Pendiente')
        for p in pending_passengers:
            p.status_id = rejected_status
            p.save()
            
        # Nota: La desactivación de publicaciones se maneja automáticamente por signals al cambiar a 'En curso'
        
        return Response({
            "detail": "El viaje ha sido iniciado manualmente.",
            "trip_status": "En curso"
        })

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def passengers(self, request, pk=None):
        """
        Retorna el listado de pasajeros (TripPassenger) asociados a un viaje.
        """
        trip = self.get_object()
        passengers = trip.passengers.all().select_related('passenger_id', 'status_id')
        
        serializer = TripPassengerSerializer(passengers, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny], serializer_class=serializers.Serializer)
    def reset_all(self, request):
        """
        Endpoint de depuración:
        - Desactiva todas las publicaciones.
        - Cancela todos los viajes activos (Pendiente/En curso).
        - Cierra todos los chats activos.
        """
        # 1. Desactivar todas las publicaciones activas
        pub_updated = Publication.objects.filter(is_active=True).update(is_active=False)
        
        # 2. Cancelar viajes activos
        try:
            cancel_status = TripStatus.objects.get(name='Cancelado')
            trips_updated = Trip.objects.filter(status_id__name__in=['Pendiente', 'En curso']).update(
                status_id=cancel_status,
                auto_finalized=True,
                finalized_at=timezone.now()
            )
        except TripStatus.DoesNotExist:
            trips_updated = 0
            
        # 3. Cerrar todos los chats activos
        chats_updated = Chat.objects.filter(is_active=True).update(
            is_active=False,
            closed_at=timezone.now()
        )
        
        return Response({
            "message": "Sistema reseteado correctamente.",
            "publications_deactivated": pub_updated,
            "trips_canceled": trips_updated,
            "chats_closed": chats_updated
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated], serializer_class=CancelTripSerializer)
    def cancel_participation(self, request, pk=None):
        """
        Endpoint para cancelar la participación en un viaje.
        Requiere 'reason' en el body.
        Reglas:
        - Si cancela el Conductor -> El viaje pasa a 'Pendiente Cancelación'. Se espera confirmación de pasajeros.
        - Si cancela un Pasajero:
            - Si el viaje tiene > 2 integrantes (Conductor + >1 Pasajero Aceptado) -> Solo se cancela el pasajero.
            - Si el viaje tiene <= 2 integrantes (Conductor + 1 Pasajero) -> El viaje pasa a 'Pendiente Cancelación'. Se espera confirmación del conductor.
        """
        trip = self.get_object()
        user = request.user
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data['reason']

        # Verificar si el usuario es participante
        is_driver = trip.driver_id == user
        passenger_record = trip.passengers.filter(passenger_id=user).first()

        if not is_driver and not passenger_record:
            return Response(
                {"detail": "No eres participante de este viaje."}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        # Verificar estado del viaje (solo Pendiente o En curso)
        if trip.status_id.name not in ['Pendiente', 'En curso']:
            return Response(
                {"detail": "No se puede cancelar un viaje que no está activo."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            cancel_status_passenger = TripPassengerStatus.objects.get(name='Cancelado')
            pending_cancellation_status, _ = TripStatus.objects.get_or_create(name='Pendiente Cancelación')
        except Exception:
            return Response(
                {"detail": "Error de configuración: Estados necesarios no encontrados."}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Helper para iniciar cancelación del viaje (Estado Intermedio)
        def initiate_trip_cancellation(trip_obj, reason_text, canceled_by_user):
            trip_obj.status_id = pending_cancellation_status
            trip_obj.cancel_reason = reason_text
            trip_obj.canceled_by = canceled_by_user
            
            # Auto-confirmar lectura para el usuario que cancela
            if canceled_by_user == trip_obj.driver_id:
                trip_obj.driver_cancellation_ack = True
            else:
                # Si es pasajero, buscamos su record y marcamos ack
                p_rec = trip_obj.passengers.filter(passenger_id=canceled_by_user).first()
                if p_rec:
                    p_rec.cancellation_ack = True
                    p_rec.save()
            
            trip_obj.save()
            return "Se ha solicitado la cancelación del viaje. Esperando confirmación de lectura de los demás participantes."

        # Lógica de cancelación
        message = ""
        trip_status_result = trip.status_id.name # Default actual

        if is_driver:
            # Caso: Conductor cancela -> Inicia cancelación global
            message = initiate_trip_cancellation(trip, reason, user)
            trip_status_result = "Pendiente Cancelación"
        else:
            # Caso: Pasajero cancela
            # Contar pasajeros aceptados ACTIVOS (excluyendo al que cancela si ya estuviera contado, pero aun no cambiamos estado)
            # Total integrantes = 1 (Conductor) + N (Pasajeros Aceptados)
            active_passengers_count = trip.passengers.filter(status_id__name='Aceptado').count()
            total_participants = 1 + active_passengers_count
            
            # Si el pasajero actual NO está aceptado (ej. Pendiente), su salida no afecta la integridad del viaje activo.
            # Pero si está Aceptado, cuenta para la regla de "2 integrantes".
            is_accepted = passenger_record.status_id.name == 'Aceptado'
            
            if is_accepted and total_participants <= 2:
                # Caso: Conductor + 1 Pasajero (el que cancela) -> Inicia cancelación global
                message = initiate_trip_cancellation(trip, reason, user)
                trip_status_result = "Pendiente Cancelación"
            else:
                # Caso: Hay más gente o el pasajero no estaba aceptado -> Solo se va él (Inmediato)
                passenger_record.status_id = cancel_status_passenger
                passenger_record.cancel_reason = reason
                passenger_record.finalized_at = timezone.now()
                passenger_record.save()
                
                # Liberar cupos si era una oferta y estaba aceptado
                if 'oferta' in trip.publication_id.type_id.name.lower() and is_accepted:
                    from django.db.models import F
                    trip.publication_id.available_seats = F('available_seats') + passenger_record.seats_reserved
                    trip.publication_id.save()
                    trip.publication_id.refresh_from_db()

                message = "Tu participación ha sido cancelada."
                trip_status_result = trip.status_id.name # Mantiene estado original (Pendiente/En curso)

        return Response({
            "detail": message,
            "canceled_by": user.name,
            "reason": reason,
            "trip_status": trip_status_result
        })

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def confirm_cancellation_read(self, request, pk=None):
        """
        Endpoint para confirmar que el usuario ha leído el motivo de cancelación.
        Solo válido si el viaje está en 'Pendiente Cancelación'.
        Si todos los participantes confirman, el viaje pasa a 'Cancelado'.
        """
        trip = self.get_object()
        user = request.user
        
        if trip.status_id.name != 'Pendiente Cancelación':
            return Response(
                {"detail": "El viaje no está en proceso de cancelación."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Identificar rol y marcar ACK
        is_driver = trip.driver_id == user
        passenger_record = trip.passengers.filter(passenger_id=user).first()

        if not is_driver and not passenger_record:
             return Response(
                {"detail": "No eres participante de este viaje."}, 
                status=status.HTTP_403_FORBIDDEN
            )

        if is_driver:
            trip.driver_cancellation_ack = True
            trip.save()
        else:
            # Solo pasajeros aceptados necesitan confirmar (los pendientes/rechazados no pintan mucho aquí, pero asumamos aceptados)
            # De hecho, si el viaje se canceló, solo nos importan los que estaban activos.
            passenger_record.cancellation_ack = True
            passenger_record.save()

        # Verificar si TODOS han confirmado
        # Participantes que deben confirmar: Conductor + Pasajeros Aceptados
        
        # 1. Driver Ack
        if not trip.driver_cancellation_ack:
            return Response({"detail": "Confirmación registrada. Esperando al conductor."})

        # 2. Passengers Ack
        # Buscamos pasajeros que estaban Aceptados
        pending_passengers = trip.passengers.filter(status_id__name='Aceptado', cancellation_ack=False).exists()
        
        if not pending_passengers:
            # Todos confirmaron -> FINALIZAR CANCELACIÓN
            try:
                cancel_status_trip = TripStatus.objects.get(name='Cancelado')
                cancel_status_passenger = TripPassengerStatus.objects.get(name='Cancelado')
            except:
                 return Response({"detail": "Error interno configurando estados."}, status=500)

            trip.status_id = cancel_status_trip
            trip.finalized_at = timezone.now()
            trip.save()
            
            # Desactivar publicación
            trip.publication_id.is_active = False
            trip.publication_id.save()
            
            # Cancelar a todos los pasajeros activos
            trip.passengers.filter(status_id__name__in=['Pendiente', 'Aceptado']).update(
                status_id=cancel_status_passenger,
                cancel_reason=f"Viaje cancelado por {trip.canceled_by.name if trip.canceled_by else 'Desconocido'}: {trip.cancel_reason}",
                finalized_at=timezone.now()
            )
            
            # Cerrar chats
            Chat.objects.filter(publication=trip.publication_id, is_active=True).update(
                is_active=False,
                closed_at=timezone.now()
            )
            
            return Response({
                "detail": "Confirmación registrada. El viaje ha sido cancelado completamente.",
                "trip_status": "Cancelado"
            })
            
        return Response({
            "detail": "Confirmación registrada. Esperando a los demás participantes.",
            "trip_status": "Pendiente Cancelación"
        })
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated], serializer_class=serializers.Serializer)
    def finalize(self, request, pk=None):
        """
        El viaje solo cambia a estado 'Finalizado' globalmente cuando TODOS los participantes
        (conductor y pasajeros aceptados) lo han marcado como finalizado.
        """
        trip = self.get_object()
        user = request.user
        
        # Verificar si el usuario es participante
        is_driver = trip.driver_id == user
        passenger_record = trip.passengers.filter(passenger_id=user).first()
        
        if not is_driver and not passenger_record:
            return Response(
                {"detail": "No eres participante de este viaje."}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        try:
            finalized_status = TripStatus.objects.get(name='Finalizado')
            pending_finalized_status, _ = TripStatus.objects.get_or_create(name='Pendiente finalizado')
            passenger_finalized_status = TripPassengerStatus.objects.get(name='Finalizado')
        except (TripStatus.DoesNotExist, TripPassengerStatus.DoesNotExist):
            return Response(
                {"detail": "Error de configuración: Estado 'Finalizado' no encontrado."}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        if is_driver:
            trip.driver_finalized = True
            trip.save()
        else:
            if passenger_record.status_id.name not in ['Aceptado', 'Finalizado']:
                 return Response(
                    {"detail": "Solo pasajeros aceptados pueden finalizar el viaje."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            passenger_record.status_id = passenger_finalized_status
            passenger_record.finalized_at = timezone.now()
            passenger_record.save()
            
        trip.refresh_from_db()
        
        all_passengers_done = not trip.passengers.filter(status_id__name='Aceptado').exists()
        any_passenger_finalized = trip.passengers.filter(status_id__name='Finalizado').exists()
        
        if trip.driver_finalized and all_passengers_done:
            trip.status_id = finalized_status
            trip.finalized_at = timezone.now()
            trip.save()
            
            # Desactivar publicación asociada
            trip.publication_id.is_active = False
            trip.publication_id.save()
            
            # Cerrar chats asociados
            Chat.objects.filter(publication=trip.publication_id, is_active=True).update(
                is_active=False,
                closed_at=timezone.now()
            )
            
            return Response({
                "detail": "Has marcado el viaje como finalizado. El viaje ha concluido para todos.",
                "trip_status": "Finalizado"
            })
            
        if trip.driver_finalized or any_passenger_finalized:
            if trip.status_id != pending_finalized_status:
                trip.status_id = pending_finalized_status
                trip.save(update_fields=['status_id'])
            
        return Response({
            "detail": "Has marcado el viaje como finalizado. Esperando a los demás participantes.",
            "trip_status": trip.status_id.name
        })

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def finalization_status(self, request, pk=None):
        trip = self.get_object()
        finalized_members = []
        pending_members = []

        driver_data = SimpleUserSerializer(trip.driver_id).data
        driver_data['role'] = 'Conductor'
        if trip.driver_finalized:
            finalized_members.append(driver_data)
        else:
            pending_members.append(driver_data)

        passengers_qs = trip.passengers.filter(
            status_id__name__in=['Aceptado', 'Finalizado']
        ).select_related('passenger_id', 'status_id')

        for tp in passengers_qs:
            data = SimpleUserSerializer(tp.passenger_id).data
            data['role'] = 'Pasajero'
            if tp.status_id.name == 'Finalizado':
                finalized_members.append(data)
            else:
                pending_members.append(data)

        return Response({
            "trip_id": trip.id,
            "trip_status": trip.status_id.name,
            "finalized_members": finalized_members,
            "pending_members": pending_members
        })

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def rateable_members(self, request, pk=None):
        trip = self.get_object()
        user = request.user
        is_driver = trip.driver_id == user
        is_passenger = trip.passengers.filter(passenger_id=user).exists()
        if not is_driver and not is_passenger:
            return Response({"detail": "No eres participante de este viaje."}, status=status.HTTP_403_FORBIDDEN)
        members = []
        if is_passenger and trip.driver_id != user:
            data = SimpleUserSerializer(trip.driver_id).data
            data['role'] = 'Conductor'
            members.append(data)
        passengers_qs = trip.passengers.filter(
            status_id__name__in=['Aceptado', 'Finalizado']
        ).select_related('passenger_id', 'status_id')
        for tp in passengers_qs:
            if tp.passenger_id == user:
                continue
            data = SimpleUserSerializer(tp.passenger_id).data
            data['role'] = 'Pasajero'
            members.append(data)
        return Response({
            "trip_id": trip.id,
            "members": members
        })

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def cancellation_reason(self, request, pk=None):
        """
        Devuelve el motivo de cancelación de un viaje.
        Solo disponible si el viaje está en estado 'Cancelado'.
        """
        trip = self.get_object()
        
        if trip.status_id.name != 'Cancelado':
            return Response(
                {"detail": "El viaje no está cancelado."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        return Response({
            "cancel_reason": trip.cancel_reason,
            "finalized_at": trip.finalized_at
        })
