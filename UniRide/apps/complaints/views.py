from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.response import Response  # Retornar respuestas (Response)
# Definir quién puede acceder a cada vista (permissions)
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from apps.users.models import AuditLog, User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from apps.complaints.models import Complaint, ComplaintType, ComplaintStatus
from apps.trips.models import Trip, TripPassenger
from apps.chat.models import Chat
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.http import require_http_methods

# listar quejas activas (pendientes)
@api_view(['GET'])
@permission_classes([IsAdminUser])
@require_GET
def list_active_complaints(request):
    try:
        complaints = Complaint.objects.select_related(
            'type_id', 'status_id', 'reported_user_id', 'reporter_id'
        ).filter(
            status_id_id=1  # Pendiente
        ).order_by('-created_at')

        data = []
        for c in complaints:
            data.append({
                "id": c.id,
                "type": {
                    "id": c.type_id.id,
                    "name": c.type_id.name
                },
                "description": c.description,
                "reported_user": {
                    "id": c.reported_user_id.id,
                    "name": c.reported_user_id.name
                }if c.reported_user_id else None,
                 "reporter": {
                    "id": c.reporter_id.id,
                    "name": c.reporter_id.name
                },
                "created_at": c.created_at
            })

        return Response(data, status=200)
    except Exception as e:
        return Response(
            {"detail": "Ocurrió un error al listar las quejas activas.", "error": str(e)},
            status=500
        )

# resolver queja
@api_view(['POST'])
@permission_classes([IsAdminUser])
@require_POST
def resolve_complaint(request, complaint_id):
    try:
        complaint = get_object_or_404(
            Complaint,
            id=complaint_id,
            status_id_id=1  # Solo pendientes
        )

        complaint.status_id_id = 2  # Resuelta
        complaint.resolved_at = timezone.now()
        complaint.admin_id = request.user
        complaint.save(update_fields=[
            "status_id",
            "resolved_at",
            "admin_id"
        ])

        # 🧾 Auditoría
        AuditLog.objects.create(
            actor=request.user,
            action="RESOLVER_QUEJA",
            target_user=complaint.reported_user_id,
            extra_data={
                "complaint_id": complaint.id,
                "type": complaint.type_id.name
            }
        )

        return Response(
            {"detail": "Queja marcada como atendida"},
            status=200
        )
    except Exception as e:
        return Response(
            {"detail": "Ocurrió un error al resolver la queja.", "error": str(e)},
            status=500
        )


# --- Nuevos Endpoints para Usuarios ---

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_GET
def get_interactable_users(request):
    """
    Obtiene la lista de usuarios con los que el usuario actual ha interactuado
    en viajes (como conductor o pasajero) o en chats.
    """
    try:
        user = request.user
        interacted_user_ids = set()

        # 1. Interacciones en Viajes
        # Como conductor: obtener todos los pasajeros aceptados o que finalizaron el viaje
        trips_as_driver = Trip.objects.filter(driver_id=user).values_list('id', flat=True)
        passengers_in_driven_trips = TripPassenger.objects.filter(
            trip_id__in=trips_as_driver,
            status_id__name__in=['Aceptado', 'Finalizado']
        ).values_list('passenger_id', flat=True)
        interacted_user_ids.update(passengers_in_driven_trips)

        # Como pasajero: obtener el conductor y otros pasajeros aceptados del mismo viaje
        trips_where_passenger = TripPassenger.objects.filter(
            passenger_id=user,
            status_id__name__in=['Aceptado', 'Finalizado']
        ).values_list('trip_id', flat=True)
        
        # Conductores de esos viajes
        drivers_of_trips = Trip.objects.filter(id__in=trips_where_passenger).values_list('driver_id', flat=True)
        interacted_user_ids.update(drivers_of_trips)
        
        # Otros pasajeros de esos mismos viajes
        other_passengers = TripPassenger.objects.filter(
            trip_id__in=trips_where_passenger,
            status_id__name__in=['Aceptado', 'Finalizado']
        ).exclude(passenger_id=user).values_list('passenger_id', flat=True)
        interacted_user_ids.update(other_passengers)

        # 2. Interacciones en Chats
        chats_as_passenger = Chat.objects.filter(passenger=user).values_list('driver', flat=True)
        chats_as_driver = Chat.objects.filter(driver=user).values_list('passenger', flat=True)
        interacted_user_ids.update(chats_as_passenger)
        interacted_user_ids.update(chats_as_driver)

        # Eliminar al propio usuario si está en la lista
        interacted_user_ids.discard(user.id)

        # Obtener detalles de los usuarios (solo id y nombre para la selección)
        users = User.objects.filter(id__in=interacted_user_ids).values('id', 'name')

        return Response(list(users), status=200)
    
    except Exception as e:
        return Response(
            {"detail": "Ocurrió un error al obtener la lista de usuarios interactuables.", "error": str(e)},
            status=500
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_POST
def create_complaint(request):
    """
    Crea una queja de tipo Técnica (Bug/Recomendación) o de Comportamiento.
    """
    try:
        user = request.user
        data = request.data

        type_name = data.get('type')  # Esperado: 'Técnica' o 'Comportamiento'
        description = data.get('description')
        reported_user_id = data.get('reported_user_id')
        trip_id = data.get('trip_id')

        # Validaciones básicas
        if not type_name or not description:
            return Response(
                {"detail": "El tipo de queja y la descripción son obligatorios."},
                status=400
            )

        # Validar tipo de queja
        try:
            complaint_type = ComplaintType.objects.get(name=type_name)
        except ComplaintType.DoesNotExist:
            return Response(
                {"detail": f"El tipo de queja '{type_name}' no existe en el sistema."},
                status=400
            )

        # El estado inicial siempre es 'Pendiente' (ID 1 según lógica existente)
        try:
            status_pendiente = ComplaintStatus.objects.get(id=1)
        except ComplaintStatus.DoesNotExist:
            status_pendiente, _ = ComplaintStatus.objects.get_or_create(name='Pendiente')

        reported_user = None
        
        # Lógica específica para quejas de Comportamiento
        if type_name == 'Comportamiento':
            if not reported_user_id:
                return Response(
                    {"detail": "Para reportar comportamiento se debe especificar a un usuario."},
                    status=400
                )
            
            # Verificar interacción previa
            has_interacted = False
            
            # Verificar en viajes
            # Caso 1: El reportero es conductor y el reportado es pasajero aceptado
            if TripPassenger.objects.filter(
                trip_id__driver_id=user,
                passenger_id=reported_user_id,
                status_id__name__in=['Aceptado', 'Finalizado']
            ).exists():
                has_interacted = True
                
            # Caso 2: El reportero es pasajero aceptado y el reportado es el conductor
            if not has_interacted and Trip.objects.filter(
                driver_id=reported_user_id,
                passengers__passenger_id=user,
                passengers__status_id__name__in=['Aceptado', 'Finalizado']
            ).exists():
                has_interacted = True
                
            # Caso 3: Ambos son pasajeros aceptados en el mismo viaje
            if not has_interacted:
                trips_reporter = TripPassenger.objects.filter(
                    passenger_id=user,
                    status_id__name__in=['Aceptado', 'Finalizado']
                ).values_list('trip_id', flat=True)
                
                if TripPassenger.objects.filter(
                    trip_id__in=trips_reporter,
                    passenger_id=reported_user_id,
                    status_id__name__in=['Aceptado', 'Finalizado']
                ).exists():
                    has_interacted = True

            # Verificar en chats
            if not has_interacted:
                if Chat.objects.filter(passenger=user, driver_id=reported_user_id).exists() or \
                   Chat.objects.filter(driver=user, passenger_id=reported_user_id).exists():
                    has_interacted = True

            if not has_interacted:
                return Response(
                    {"detail": "No puedes reportar a un usuario con el que no has interactuado."},
                    status=403
                )
            
            reported_user = get_object_or_404(User, id=reported_user_id)

        # Crear la queja
        complaint = Complaint.objects.create(
            reporter_id=user,
            reported_user_id=reported_user,
            type_id=complaint_type,
            trip_id_id=trip_id,
            description=description,
            status_id=status_pendiente
        )

        return Response({
            "detail": "Queja registrada correctamente.",
            "complaint_id": complaint.id
        }, status=201)

    except Exception as e:
        return Response(
            {"detail": "Ocurrió un error al registrar la queja.", "error": str(e)},
            status=500
        )


# --- Endpoints para Tipos de Quejas (ComplaintType) ---
@api_view(['GET'])
@permission_classes([IsAdminUser])
@require_GET
def get_complaint_types(request):
    types = ComplaintType.objects.all().values('id', 'name', 'description')
    return Response(list(types), status=200)


@api_view(['POST'])
@permission_classes([IsAdminUser])
@require_POST
def create_complaint_type(request):
    name = request.data.get('name')
    description = request.data.get('description', '')

    if not name:
        return Response({"detail": "El nombre es obligatorio."}, status=400)

    complaint_type, created = ComplaintType.objects.get_or_create(
        name=name,
        defaults={'description': description}
    )

    if not created:
        return Response({"detail": "Ya existe."}, status=400)

    return Response({
        "detail": "Creado correctamente",
        "id": complaint_type.id
    }, status=201)

# --- Endpoints para Estados de Quejas (ComplaintStatus) ---
@api_view(['GET'])
@permission_classes([IsAdminUser])
@require_GET
def get_complaint_status(request):
    statuses = ComplaintStatus.objects.all().values('id', 'name')
    return Response(list(statuses), status=200)


@api_view(['POST'])
@permission_classes([IsAdminUser])
@require_POST
def create_complaint_status(request):
    name = request.data.get('name')

    if not name:
        return Response({"detail": "El nombre del estado es obligatorio."}, status=400)

    status_obj, created = ComplaintStatus.objects.get_or_create(name=name)

    if not created:
        return Response({"detail": "Ya existe."}, status=400)

    return Response({
        "detail": "Estado creado correctamente",
        "id": status_obj.id
    }, status=201)