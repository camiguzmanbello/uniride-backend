from django.utils import timezone
from django.utils import timezone

def build_suspension_data(suspensions, today):
    data = []

    for s in suspensions:
        end_date = s.end_date.date() if s.end_date else None

        item = {
            "user": s.user_id.name,
            "admin": s.admin_id.name,
            "start": s.start_date.strftime("%d/%m/%Y"),
            "end": s.end_date.strftime("%d/%m/%Y") if s.end_date else None,
            "is_permanent": s.is_permanent,
        }

        if s.is_permanent:
            item.update({
                "type": "Permanente",
                "status": "ACTIVA",
                "days_remaining": None,
            })
        else:
            if end_date and end_date >= today:
                item.update({
                    "type": "Temporal",
                    "status": "ACTIVA",
                    "days_remaining": (end_date - today).days,
                })
            else:
                item.update({
                    "type": "Temporal",
                    "status": "VENCIDA",
                    "days_remaining": 0,
                })

        data.append(item)

    return data