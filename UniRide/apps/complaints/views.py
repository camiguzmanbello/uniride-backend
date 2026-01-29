from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.response import Response  # Retornar respuestas (Response)
# Definir quién puede acceder a cada vista (permissions)
from rest_framework.permissions import IsAdminUser
from apps.users.models import AuditLog
from apps.users.serializer import *
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from apps.complaints.models import Complaint
# listar quejas activas (pendientes)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_active_complaints(request):
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
# resolver queja
@api_view(['POST'])
@permission_classes([IsAdminUser])
def resolve_complaint(request, complaint_id):
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
