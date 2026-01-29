from django.utils import timezone
def build_suspension_data(suspensions):
    today = timezone.now().date()
    data = []

    for s in suspensions:
        item = {
            "user": s.user_id.name,
            "admin": s.admin_id.name,
            "start": s.start_date,
            "end": s.end_date,
            "is_permanent": s.is_permanent,
        }

        if s.is_permanent:
            item.update({
                "type": "Permanente",
                "status": "ACTIVA",
                "days_remaining": None,
            })
        else:
            if s.end_date and s.end_date >= today:
                item.update({
                    "type": "Temporal",
                    "status": "ACTIVA",
                    "days_remaining": (s.end_date - today).days,
                })
            else:
                item.update({
                    "type": "Temporal",
                    "status": "VENCIDA",
                    "days_remaining": 0,
                })

        data.append(item)

    return data

