# apps/core/utils/reports.py
from django.utils import timezone
from django.templatetags.static import static

def get_report_base_context(title, subtitle: str, user=None):
    return {
        "report_title": title,
        "report_subtitle": subtitle,
        "generated_at": timezone.now().strftime("%d/%m/%Y %H:%M"),
        "generated_by": user.name if user else "Sistema",
        "logo_url": static("reports_assets/uniride_logo.png"),
    }
