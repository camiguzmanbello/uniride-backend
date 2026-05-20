from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from .models import Chat, Message
from apps.trips.models import Publication
from .serializers import ChatListSerializer, ChatCreateSerializer, MessageSerializer
from .permissions import IsChatParticipant
from apps.trips.serializers import InterestSerializer
from apps.trips.services.trip_flow import create_interest
from apps.users.utils.login_payload_crypto import decrypt_payload, PayloadDecryptionError
import logging

logger = logging.getLogger(__name__)

class ChatViewSet(viewsets.ModelViewSet):
    """
    ViewSet para manejar chats.
    Permite crear, listar, ver detalle y cerrar chats.
    También maneja el envío y listado de mensajes.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ChatCreateSerializer
        return ChatListSerializer

    def get_queryset(self):
        """
        Retorna los chats donde el usuario es pasajero o conductor.
        """
        user = self.request.user
        return Chat.objects.filter(
            Q(passenger=user) | Q(driver=user)
        ).select_related('publication', 'passenger', 'driver').prefetch_related('messages').order_by('-created_at')

    def get_permissions(self):
        """
        Para acciones de detalle, validamos que sea participante.
        """
        if self.action in ['retrieve', 'messages', 'close']:
            return [permissions.IsAuthenticated(), IsChatParticipant()]
        return super().get_permissions()

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """
        Cierra un chat activo. Solo permitido para el conductor.
        """
        chat = self.get_object()
        
        # Regla: Solo el conductor puede cerrar el chat
        if request.user != chat.driver:
            return Response(
                {"detail": "Solo el conductor puede cerrar el chat."}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        if not chat.is_active:
            return Response(
                {"detail": "El chat ya está cerrado."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        chat.is_active = False
        chat.closed_at = timezone.now()
        chat.save()
        return Response({"detail": "Chat cerrado exitosamente."})

    def create(self, request, *args, **kwargs):
        data = request.data
        try:
            data = data.copy()
        except Exception:
            pass

        if isinstance(data, dict) and data.get("payload") is not None:
            try:
                decrypted = decrypt_payload(data.get("payload"))
                for k, v in decrypted.items():
                    data[k] = v
            except PayloadDecryptionError as e:
                logger.warning(f"Error descifrando payload de creación de chat: {str(e)}")
                return Response({"error": "Payload de chat inválido"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=['get', 'post'])
    def messages(self, request, pk=None):
        """
        GET: Lista los mensajes del chat en orden cronológico.
        POST: Envía un nuevo mensaje al chat.
        """
        chat = self.get_object()
        
        if request.method == 'GET':
            # Orden cronológico (antiguos primero para leer historial)
            messages = chat.messages.all().order_by('sent_at')
            serializer = MessageSerializer(messages, many=True)
            return Response(serializer.data)
            
        elif request.method == 'POST':
            if not chat.is_active:
                return Response(
                    {"detail": "No se pueden enviar mensajes en un chat cerrado."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check TripPassenger status
            if chat.trip_passenger and chat.trip_passenger.status_id.name in ['Rechazado', 'Cancelado', 'Finalizado']:
                return Response(
                    {"detail": f"No se pueden enviar mensajes porque el estado es {chat.trip_passenger.status_id.name}."},
                    status=status.HTTP_409_CONFLICT
                )
            
            data = request.data
            try:
                data = data.copy()
            except Exception:
                pass

            if isinstance(data, dict) and data.get("payload") is not None:
                try:
                    decrypted = decrypt_payload(data.get("payload"))
                    for k, v in decrypted.items():
                        data[k] = v
                except PayloadDecryptionError as e:
                    logger.warning(f"Error descifrando payload de mensaje: {str(e)}")
                    return Response({"error": "Payload de mensaje inválido"}, status=status.HTTP_400_BAD_REQUEST)

            # Crear el mensaje
            serializer = MessageSerializer(data=data)
            if serializer.is_valid():
                # Asignamos chat y sender explícitamente
                # Nota: En models.py los campos FK se llaman chat_id y sender_id
                serializer.save(
                    chat_id=chat, 
                    sender_id=request.user
                )
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class InterestViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = InterestSerializer

    def create(self, request):
        data = request.data
        try:
            data = data.copy()
        except Exception:
            pass

        if isinstance(data, dict) and data.get("payload") is not None:
            try:
                decrypted = decrypt_payload(data.get("payload"))
                for k, v in decrypted.items():
                    data[k] = v
            except PayloadDecryptionError as e:
                logger.warning(f"Error descifrando payload de interés: {str(e)}")
                return Response({"error": "Payload de interés inválido"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        pub_id = serializer.validated_data['publication_id']
        seats = serializer.validated_data['seats_reserved']
        
        try:
            publication = Publication.objects.get(id=pub_id)
            pub_type = publication.type_id.name.lower()
            
            if 'oferta' in pub_type:
                 result = create_interest(pub_id, request.user, seats_reserved=seats)
            elif 'solicitud' in pub_type:
                 result = create_interest(pub_id, publication.user_id, seats_reserved=seats, driver_user=request.user)
            else:
                 return Response({"detail": "Tipo no soportado."}, status=status.HTTP_400_BAD_REQUEST)
                 
            return Response({
                "trip_passenger_id": result['trip_passenger'].id,
                "chat_id": result['chat'].id,
                "status": result['status']
            }, status=status.HTTP_201_CREATED)
            
        except Publication.DoesNotExist:
             return Response({"detail": "Publicación no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
             # Handle ConflictError/ValidationError
             # Re-raise to let DRF handle or handle specifically?
             # If ConflictError (APIException), DRF handles it.
             raise e
