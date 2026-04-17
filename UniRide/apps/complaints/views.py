from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.authentication import SessionAuthentication

from apps.users.models import AuditLog, User
from apps.complaints.models import Complaint, ComplaintType, ComplaintStatus
from apps.trips.models import Trip, TripPassenger
from apps.chat.models import Chat


# ================================
# 🔐 CSRF FIX PARA JWT
# ================================
class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return


# ================================
# LISTAR QUEJAS ACTIVAS
# ================================
@api_view(['GET'])
@permission_classes([IsAdminUser])
@authentication_classes([CsrfExemptSessionAuthentication])
def list_active_complaints(request):
    try:
        complaints = Complaint.objects.select_related(
            'type_id', 'status_id', 'reported_user_id', 'reporter_id'
        ).filter(
            status_id_id=1
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
                } if c.reported_user_id else None,
                "reporter": {
                    "id": c.reporter_id.id,
                    "name": c.reporter_id.name
                },
                "created_at": c.created_at
            })

        return Response(data, status=200)

    except Exception as e:
        return Response(
            {"detail": "Ocurrió un error al listar las quejas activas."},
            status=500
        )


# ================================
# RESOLVER QUEJA
# ================================
@api_view(['POST'])
@permission_classes([IsAdminUser])
@authentication_classes([CsrfExemptSessionAuthentication])
def resolve_complaint(request, complaint_id):
    try:
        complaint = get_object_or_404(
            Complaint,
            id=complaint_id,
            status_id_id=1
        )

        complaint.status_id_id = 2
        complaint.resolved_at = timezone.now()
        complaint.admin_id = request.user
        complaint.save(update_fields=[
            "status_id",
            "resolved_at",
            "admin_id"
        ])

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

    except Exception:
        return Response(
            {"detail": "Ocurrió un error al resolver la queja."},
            status=500
        )


# ================================
# USUARIOS INTERACTUABLES
# ================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([CsrfExemptSessionAuthentication])
def get_interactable_users(request):
    try:
        user = request.user
        interacted_user_ids = set()

        trips_as_driver = Trip.objects.filter(driver_id=user).values_list('id', flat=True)

        passengers = TripPassenger.objects.filter(
            trip_id__in=trips_as_driver,
            status_id__name__in=['Aceptado', 'Finalizado']
        ).values_list('passenger_id', flat=True)

        interacted_user_ids.update(passengers)

        trips_where_passenger = TripPassenger.objects.filter(
            passenger_id=user,
            status_id__name__in=['Aceptado', 'Finalizado']
        ).values_list('trip_id', flat=True)

        drivers = Trip.objects.filter(
            id__in=trips_where_passenger
        ).values_list('driver_id', flat=True)

        interacted_user_ids.update(drivers)

        other_passengers = TripPassenger.objects.filter(
            trip_id__in=trips_where_passenger,
            status_id__name__in=['Aceptado', 'Finalizado']
        ).exclude(passenger_id=user).values_list('passenger_id', flat=True)

        interacted_user_ids.update(other_passengers)

        chats_passenger = Chat.objects.filter(passenger=user).values_list('driver', flat=True)
        chats_driver = Chat.objects.filter(driver=user).values_list('passenger', flat=True)

        interacted_user_ids.update(chats_passenger)
        interacted_user_ids.update(chats_driver)

        interacted_user_ids.discard(user.id)

        users = User.objects.filter(id__in=interacted_user_ids).values('id', 'name')

        return Response(list(users), status=200)

    except Exception:
        return Response(
            {"detail": "Ocurrió un error al obtener usuarios."},
            status=500
        )


# ================================
# CREAR QUEJA
# ================================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([CsrfExemptSessionAuthentication])
def create_complaint(request):
    try:
        user = request.user
        data = request.data

        type_name = data.get('type')
        description = data.get('description')
        reported_user_id = data.get('reported_user_id')
        trip_id = data.get('trip_id')

        if not type_name or not description:
            return Response(
                {"detail": "Tipo y descripción obligatorios."},
                status=400
            )

        try:
            complaint_type = ComplaintType.objects.get(name=type_name)
        except ComplaintType.DoesNotExist:
            return Response({"detail": "Tipo inválido"}, status=400)

        status_pendiente, _ = ComplaintStatus.objects.get_or_create(name='Pendiente')

        reported_user = None

        if type_name == 'Comportamiento':
            if not reported_user_id:
                return Response({"detail": "Debe indicar usuario"}, status=400)

            reported_user = get_object_or_404(User, id=reported_user_id)

        complaint = Complaint.objects.create(
            reporter_id=user,
            reported_user_id=reported_user,
            type_id=complaint_type,
            trip_id_id=trip_id,
            description=description,
            status_id=status_pendiente
        )

        return Response(
            {"detail": "Queja registrada", "complaint_id": complaint.id},
            status=201
        )

    except Exception:
        return Response(
            {"detail": "Error al crear queja"},
            status=500
        )


# ================================
# TIPOS DE QUEJA
# ================================
@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
@authentication_classes([CsrfExemptSessionAuthentication])
def manage_complaint_types(request):
    try:
        if request.method == 'GET':
            types = ComplaintType.objects.all().values('id', 'name', 'description')
            return Response(list(types), status=200)

        name = request.data.get('name')
        if not name:
            return Response({"detail": "Nombre requerido"}, status=400)

        obj, created = ComplaintType.objects.get_or_create(name=name)

        if not created:
            return Response({"detail": "Ya existe"}, status=400)

        return Response({"id": obj.id}, status=201)

    except Exception:
        return Response({"detail": "Error"}, status=500)


# ================================
# ESTADOS DE QUEJA
# ================================
@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
@authentication_classes([CsrfExemptSessionAuthentication])
def manage_complaint_status(request):
    try:
        if request.method == 'GET':
            data = ComplaintStatus.objects.all().values('id', 'name')
            return Response(list(data), status=200)

        name = request.data.get('name')
        if not name:
            return Response({"detail": "Nombre requerido"}, status=400)

        obj, created = ComplaintStatus.objects.get_or_create(name=name)

        if not created:
            return Response({"detail": "Ya existe"}, status=400)

        return Response({"id": obj.id}, status=201)

    except Exception:
        return Response({"detail": "Error"}, status=500)