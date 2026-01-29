from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, serializers
from .serializers import *
from rest_framework.viewsets import ModelViewSet
from django.db.models import Q
from rest_framework.decorators import action
from apps.trips.services.trip_flow import accept_passenger, close_pending_for_publication
from apps.chat.models import Chat
from django.utils import timezone


class PublicationTypeViewSet(ModelViewSet):

    permission_classes = [permissions.AllowAny]

    queryset = PublicationType.objects.all()
    serializer_class = PublicationTypeSerializer


class PublicationViewSet(ModelViewSet):

    permission_classes = [permissions.AllowAny]

    queryset = Publication.objects.all()
    serializer_class = PublicationSerializer

    #para que al crear una publicacion se asigne el user logueado
    def perform_create(self, serializer):
        serializer.save(user_id=self.request.user)

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
        
        # Viajes donde soy conductor (Solo finalizados/cancelados)
        driven_trips = Trip.objects.filter(driver_id=user).exclude(
            status_id__name__in=['Pendiente', 'En curso']
        )
        
        # Viajes donde soy pasajero
        # Incluir si:
        # 1. El viaje terminó (Trip status Finalizado/Cancelado)
        # 2. O si mi participación terminó (Passenger status Rechazado/Cancelado)
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
        Retorna el viaje actual (Activo) del usuario, ya sea 'Pendiente' o 'En curso'.
        Retorna 204 No Content si no tiene viaje activo.
        """
        user = request.user
        
        # 1. Como conductor
        active_driven = Trip.objects.filter(
            driver_id=user,
            status_id__name__in=['Pendiente', 'En curso']
        ).first()
        
        if active_driven:
            serializer = TripHistorySerializer(active_driven, context={'request': request})
            return Response(serializer.data)
            
        # 2. Como pasajero aceptado
        active_joined = Trip.objects.filter(
            passengers__passenger_id=user,
            passengers__status_id__name='Aceptado',
            status_id__name__in=['Pendiente', 'En curso']
        ).first()
        
        if active_joined:
            serializer = TripHistorySerializer(active_joined, context={'request': request})
            return Response(serializer.data)
            
        return Response(status=status.HTTP_204_NO_CONTENT)

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
