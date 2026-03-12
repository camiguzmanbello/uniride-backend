# admin/views/dashboard_view.py
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from django.db.models.functions import TruncDate
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponse

from apps.users.models import User, AuditLog, UserSuspension
from apps.trips.models import Trip
from apps.ratings.models import Rating
from apps.complaints.models import Complaint
from apps.core.serializer import AdminDashboardSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from apps.core.serializer import UserReportSerializer, TripReportSerializer, AdminConfirmationSerializer
from django.contrib.auth import get_user_model
User = get_user_model()
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from django.template.loader import render_to_string
from xhtml2pdf import pisa
from apps.core.utils.report_context import get_report_base_context
from apps.core.utils.pdf import link_callback
from apps.core.services.user_report_service import get_user_report_data, group_users
from apps.core.services.trip_report_service import get_trip_report_queryset 
from apps.core.services.audit_report_service import group_audit_logs
from apps.core.services.suspension_report_service import build_suspension_data
from apps.core.utils.reportsFilters import apply_audit_filters


class AdminDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        today = timezone.localdate()
        start_date = today - timedelta(days=6)


        # =========================
        # Usuarios
        # =========================
        active_users = User.objects.filter(
            role_id=2,
            is_active=True,
            is_suspended=False
        ).count()

        suspended_users = User.objects.filter(
            role_id=2,
            is_suspended=True
        ).count()

        # =========================
        # Viajes activos
        # =========================
        active_trips = Trip.objects.filter(
            publication_id__is_active=True,
            finalized_at__isnull=True
        ).exclude(
            status_id__name__in=["Cancelado", "Finalizado"]
        ).count()

        # =========================
        # Quejas pendientes
        # =========================
        pending_complaints = Complaint.objects.filter(
            status_id__name="Pendiente"
        ).count()

        # =========================
        # Viajes finalizados últimos 7 días
        # =========================
        days = [start_date + timedelta(days=i) for i in range(7)]
        trip_map = {day: 0 for day in days}

        trips_week = (
            Trip.objects.filter(
                finalized_at__date__range=(start_date, today),
                status_id__name="Finalizado"
            )
            .annotate(day=TruncDate("finalized_at"))
            .values("day")
            .annotate(total=Count("id"))
        )


        for item in trips_week:
            trip_map[item["day"]] = item["total"]

        trips_per_day_labels = [day.strftime("%Y-%m-%d") for day in days]
        trips_per_day_values = [trip_map[day] for day in days]

        # =========================
        #  Viajes cancelados vs finalizados
        # =========================
        cancelled_trips = Trip.objects.filter(
            status_id__name="Cancelado",
            publication_id__departure_datetime__date__range=(start_date, today)
        ).count()

        finalized_trips = Trip.objects.filter(
            status_id__name="Finalizado",
            publication_id__departure_datetime__date__range=(start_date, today)
        ).count()



        # =========================
        # 📦 Response final
        # =========================
        data = {
            # KPIs
            "active_users": active_users,
            "suspended_users": suspended_users,
            "active_trips": active_trips,
            "pending_complaints": pending_complaints,

            # Charts
            "charts": {
                "trips_per_day": {
                    "labels": trips_per_day_labels,
                    "values": trips_per_day_values,
                },
                "trip_status": {
                    "labels": ["Cancelados", "Finalizados"],
                    "values": [cancelled_trips, finalized_trips],
                },
                "users_status": {
                    "labels": ["Activos", "Suspendidos"],
                    "values": [active_users, suspended_users],
                },
            }
        }

        return Response(AdminDashboardSerializer(data).data)
    

# ------------------------
# Helper PDF generator
# ------------------------
def generate_pdf(template_src, context, filename="reporte"):
    html = render_to_string(template_src, context)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}.pdf"'

    pisa_status = pisa.CreatePDF(
        html,
        dest=response,
        link_callback=link_callback  
    )

    if pisa_status.err:
        return HttpResponse("Error generando PDF", status=500)

    return response



# R E P O R T E S

# -------------------
# Usuarios
# -------------------
# 1. Previsualización de usuarios
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminUser])
def user_preview(request):
    user_type = request.GET.get("type", "all")

    data = get_user_report_data(user_type)

    users_data = UserReportSerializer(data["users"], many=True).data
    confirmations = AdminConfirmationSerializer(
        data["confirm_logs"], many=True
    ).data

    return Response({
        "users": users_data,
        "admin_confirmations": confirmations
    })

# 2. Generar PDF de usuarios
class UserReportPDFView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        user_type = request.GET.get("type", "all")
        data = get_user_report_data(user_type)

        generated_by = request.user.name or request.user.email

        context = {
            "report_title": "Reporte de Usuarios",
            "report_subtitle": "Usuarios activos del sistema",
            "generated_at": timezone.now().strftime("%d/%m/%Y %H:%M"),
            "generated_by": generated_by,
            "grouped_users": group_users(data["users"]),
            "confirm_logs": data["confirm_logs"],
            "total_users": data["users"].count(),
        }

        return generate_pdf(
            template_src="reports/user_report.html",
            context=context,
            filename="reporte_usuarios"
        )


# -------------------
# Viajes
# -------------------
# 1. Previsualización de viajes
class TripReportPreviewView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    def get(self, request):
        trips = get_trip_report_queryset(request)
        serializer = TripReportSerializer(trips, many=True)
        return Response(serializer.data)

# 2. Generar PDF de viajes
class TripReportPDFView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    def get(self, request):
        trips = get_trip_report_queryset(request)

        serializer = TripReportSerializer(trips, many=True)

        context = get_report_base_context(
            title="Reporte de Viajes",
            subtitle="Historial de viajes",
            user=request.user if request.user.is_authenticated else None,
        )
        context["trips"] = serializer.data

        return generate_pdf(
            template_src="reports/trip_report.html",
            context=context,
            filename="reporte_viajes"
        )

# -------------------
# Calificaciones
# -------------------
# 1. Previsualización de calificaciones
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminUser])
def rating_preview(request):
    ratings = (
        Rating.objects
        .select_related("reviewer_id", "reviewed_id")
        .order_by("-created_at")
    )

    users = {}

    for r in ratings:
        uid = r.reviewed_id.id

        if uid not in users:
            users[uid] = {
                "user": r.reviewed_id.name,
                "average": 0,
                "total": 0,
                "ratings": []
            }

        users[uid]["ratings"].append({
            "reviewer": r.reviewer_id.name,
            "stars": r.stars,
            "comment": r.comment,
            "date": r.created_at,
        })

    for u in users.values():
        total = len(u["ratings"])
        u["total"] = total
        u["average"] = round(
            sum(r["stars"] for r in u["ratings"]) / total, 2
        )

    return Response({
        "total_ratings": ratings.count(),
        "users": list(users.values())
    })
# 2. Generar PDF de calificaciones
class RatingReportPDFView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    def get(self, request):

        ratings = (
            Rating.objects
            .select_related("reviewer_id", "reviewed_id")
            .order_by("-created_at")
        )

        users = {}

        for r in ratings:
            uid = r.reviewed_id.id

            if uid not in users:
                users[uid] = {
                    "user": r.reviewed_id,
                    "ratings": [],
                }

            users[uid]["ratings"].append(r)

        user_blocks = []
        for data in users.values():
            total = len(data["ratings"])
            avg = round(
                sum(r.stars for r in data["ratings"]) / total, 2
            ) if total > 0 else 0

            user_blocks.append({
                "user": data["user"],
                "average": avg,
                "total": total,
                "ratings": data["ratings"],
            })

        context = {
            "report_title": "Reporte de Calificaciones",
            "report_subtitle": "Calificaciones recibidas por usuario",
            "generated_at": timezone.now().strftime("%d/%m/%Y %H:%M"),
            "generated_by": (
                request.user.name if request.user.is_authenticated else "Sistema"
            ),
            "users": user_blocks,
            "total": ratings.count(),
        }

        return generate_pdf(
            "reports/rating_report.html",
            context,
            "reporte_calificaciones"
        )
# -------------------
# Quejas
# -------------------
# 1. Previsualización de quejas
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminUser])
def complaint_preview(request):
    from apps.core.services.complaint_report_service import (
        get_complaint_queryset,
        split_complaints,
        serialize_complaint,
    )

    complaints = get_complaint_queryset(request)
    technical, behavioral = split_complaints(complaints)

    return Response({
        "total": complaints.count(),
        "behavioral_total": behavioral.count(),
        "technical_total": technical.count(),
        "behavioral": [serialize_complaint(c) for c in behavioral],
        "technical": [serialize_complaint(c) for c in technical],
    })

# 2. Generar PDF de quejas
class ComplaintReportPDFView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    def get(self, request):
        from apps.core.services.complaint_report_service import (
            get_complaint_queryset,
            split_complaints,
        )

        complaints = get_complaint_queryset(request)
        technical, behavioral = split_complaints(complaints)

        context = {
            "report_title": "Reporte de Quejas",
            "report_subtitle": "Quejas técnicas y de comportamiento",
            "generated_at": timezone.now().strftime("%d/%m/%Y %H:%M"),
            "generated_by": (
                request.user.name if request.user.is_authenticated else "Sistema"
            ),

            "technical_complaints": technical,
            "behavioral_complaints": behavioral,

            "total": complaints.count(),
            "total_behavioral": behavioral.count(),
            "total_technical": technical.count(),
        }

        return generate_pdf(
            "reports/complaint_report.html",
            context,
            "reporte_quejas"
        )


# -------------------
# Auditoria
# -------------------
ACTION_LABELS = {
    "LOGIN_EXITOSO": "Inicio de sesión exitoso",
    "LOGIN_FALLIDO": "Intento de inicio de sesión fallido",
    "ACTUALIZAR_PERFIL": "Actualización de perfil",
    "ACCION_REGISTRO_ADMIN": "Confirmación de registro de administrador",
    "SOFT_DELETE_ADMIN": "Desactivación de administrador",
    "SUSPENDER_USUARIO": "Suspensión de usuario",
    "RESOLVER_QUEJA": "Resolución de queja",
    "LOGIN_BLOQUEADO_SUSPENSION": "Inicio de sesión bloqueado por suspensión",
}
# 1. Previsualización de logs de auditoría
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminUser])
def audit_preview(request):
    logs = (
        AuditLog.objects
        .select_related("actor", "target_user")
        .order_by("-timestamp")
    )

    logs = apply_audit_filters(logs, request)

    grouped = group_audit_logs(logs)

    return Response({
        "total": logs.count(),
        "actions": grouped
    })

# 2. Generar PDF de logs de auditoría
class AuditReportPDFView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    def get(self, request):
        logs = (
            AuditLog.objects
            .select_related("actor", "target_user")
            .order_by("-timestamp")
        )

        logs = apply_audit_filters(logs, request)

        sections = dict(group_audit_logs(logs))

        context = {
            "report_title": "Reporte de Auditoría",
            "report_subtitle": "Eventos críticos del sistema",
            "generated_at": timezone.now().strftime("%d/%m/%Y %H:%M"),
            "generated_by": (
                request.user.name
                if request.user.is_authenticated
                else "Sistema"
            ),
            "sections": sections,
            "total": logs.count(),
        }

        return generate_pdf(
            "reports/audit_report.html",
            context,
            "reporte_auditoria"
        )


# -------------------
# Suspensiones
# -------------------
# 1. Previsualización de suspensiones
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminUser])
def suspension_preview(request):
    suspensions = UserSuspension.objects.select_related(
        "user_id", "admin_id"
    ).order_by("-start_date")

    today = timezone.now().date()

    data = build_suspension_data(suspensions, today)

    return Response({
        "total": len(data),
        "results": data
    })

# 2. Generar PDF de suspensiones
class SuspensionReportPDFView(APIView):

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):

        suspensions = UserSuspension.objects.select_related(
            "user_id", "admin_id"
        ).order_by("-start_date")

        today = timezone.now().date()

        data = build_suspension_data(suspensions, today)

        permanent_suspensions = [
            s for s in data if s["is_permanent"]
        ]

        temporary_active = [
            s for s in data if not s["is_permanent"] and s["status"] == "ACTIVA"
        ]

        temporary_expired = [
            s for s in data if not s["is_permanent"] and s["status"] == "VENCIDA"
        ]

        context = {
            "report_title": "Reporte de Suspensiones",
            "report_subtitle": "Suspensiones permanentes y temporales",
            "generated_at": timezone.now().strftime("%d/%m/%Y %H:%M"),
            "generated_by": request.user.name if request.user.is_authenticated else "Sistema",

            "total": len(data),

            "total_permanent": len(permanent_suspensions),
            "total_temp_active": len(temporary_active),
            "total_temp_expired": len(temporary_expired),

            "permanent_suspensions": permanent_suspensions,
            "temporary_active": temporary_active,
            "temporary_expired": temporary_expired,
        }

        return generate_pdf(
            "reports/suspension_report.html",
            context,
            "reporte_suspensiones"
        )