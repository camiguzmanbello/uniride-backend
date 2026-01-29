from django.utils import timezone
from apps.users.models import UserSuspension

def check_and_handle_suspension(user):
    """
    Retorna:
    - None → no está suspendido
    - dict → info de suspensión activa
    """

    # Si el usuario NO está marcado como suspendido, no hacemos nada
    if not user.is_suspended:
        return None

    now = timezone.now()

    # Tomamos la última suspensión registrada
    suspension = (
        UserSuspension.objects
        .filter(user_id=user)
        .order_by('-start_date')
        .first()
    )

    if not suspension:
        # Estado inconsistente → lo corregimos
        user.is_suspended = False
        user.save(update_fields=["is_suspended"])
        return None

    # Suspensión temporal vencida
    if (
        not suspension.is_permanent and
        suspension.end_date and
        suspension.end_date <= now
    ):
        user.is_suspended = False
        user.save(update_fields=["is_suspended"])
        return None

    # 🔒 Sigue suspendido
    remaining_days = None
    if not suspension.is_permanent and suspension.end_date:
        remaining_days = (suspension.end_date.date() - now.date()).days

    return {
        "is_permanent": suspension.is_permanent,
        "remaining_days": remaining_days,
        "reason": suspension.reason
    }
