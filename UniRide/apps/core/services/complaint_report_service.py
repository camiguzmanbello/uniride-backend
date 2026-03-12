# core/services/complaint_report_service.py

from apps.complaints.models import Complaint
from apps.core.utils.reportsFilters import apply_date_status_filters 


def get_complaint_queryset(request):
    """
    Query base de quejas con filtros aplicados
    """
    queryset = (
        Complaint.objects
        .select_related(
            "reporter_id",
            "reported_user_id",
            "type_id",
            "status_id",
            "admin_id",
        )
        .order_by("-created_at")
    )

    return apply_date_status_filters(
        queryset,
        request,
        date_field="created_at"
    )


def split_complaints(queryset):
    """
    Divide quejas técnicas y de comportamiento
    """
    technical = queryset.filter(reported_user_id__isnull=True)
    behavioral = queryset.filter(reported_user_id__isnull=False)

    return technical, behavioral


def serialize_complaint(c):
    return {
        "reporter": c.reporter_id.name,
        "reported": c.reported_user_id.name if c.reported_user_id else None,
        "type": c.type_id.name,
        "status": c.status_id.name,
        "description": c.description,
        "date": c.created_at,
        "resolved_by": c.admin_id.name if c.admin_id else None,
    }
