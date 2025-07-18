from apps.users.models import AuditLog
from django.utils.timezone import now

def registrar_log(actor, action, target_user=None, reason=None, extra_data=None):
    AuditLog.objects.create(
        actor=actor,
        action=action,
        target_user=target_user,
        reason=reason,
        extra_data=extra_data or {},
        timestamp=now()
    )