from collections import defaultdict
from apps.users.models import AuditLog, User, Vehicle
from django.db.models import Prefetch


def get_user_report_data(user_type="all"):
    users = (
        User.objects
        .filter(is_active=True)
        .select_related("role_id")
        .prefetch_related(
            Prefetch(
                "vehicles",
                queryset=Vehicle.objects.filter(is_active=True)
            )
        )
        .order_by("role_id__name", "name")
    )


    if user_type == "admin":
        users = users.filter(role_id__name="Administrador")
    elif user_type == "user":
        users = users.filter(role_id__name="Usuario")

    # 🔑 Logs de confirmación de administradores
    confirm_logs = (
        AuditLog.objects
        .filter(
            action="ACCION_REGISTRO_ADMIN",
            target_user__is_active=True,
            target_user__role_id__name="Administrador"
        )
        .select_related("actor", "target_user")
    )
    return {
        "users": users,
        "confirm_logs": confirm_logs,
        "user_type": user_type
    }
from collections import defaultdict

def group_users(users):
    grouped = defaultdict(list)
    for user in users:
        role = user.role_id.name if user.role_id else "Sin rol"
        grouped[role].append(user)
    return dict(grouped)
