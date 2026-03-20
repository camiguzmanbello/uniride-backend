from django.utils import timezone
import random
from apps.users.models import PendingUser
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from email.mime.image import MIMEImage
from pathlib import Path
from django.utils.html import strip_tags
import os

def generate_verification_code():
    """Genera un código único de 6 dígitos no expirado."""
    while True:
        code = str(random.randint(100000, 999999))
        if not PendingUser.objects.filter(code=code, expires_at__gt=timezone.now()).exists():
            return code

def send_code_email(subject: str, message: str, finalmessage: str, email: str, code: str = None, link_url: str = None, link_text: str = None) -> None:
    from_email = settings.DEFAULT_FROM_EMAIL
    
    if link_url:
        middle_html = f"""
        <p class="center">
            <a href="{link_url}" class="button">{link_text or 'Click Aquí'}</a>
        </p>
        <p class="center" style="margin-top: 12px;">
            Si el botón no funciona, copia y pega este enlace en tu navegador:<br><br>
            <a href="{link_url}" style="color:#0F5A4B;">
                {link_url}
            </a>
        </p>
        """
        middle_text = f"{link_text or 'Enlace'}: {link_url}"
    elif code:
        middle_html = f"""
        <div class="code-box">
            {code}
        </div>
        """
        middle_text = f"Código: {code}"
    else:
        middle_html = ""
        middle_text = ""

    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <link href="https://fonts.cdnfonts.com/css/clear-sans" rel="stylesheet">
    <style>
        body {{
            background: #F0F2F5; 
            font-family: 'Clear Sans', Arial, sans-serif;
            padding: 30px;
            color: #2B2B2B;
        }}
        .container {{
            max-width: 620px;
            margin: auto;
            background: #FFFFFF;
            border-radius: 18px;
            padding: 40px;
            border: 1px solid #E2E8F0;
            box-shadow: 0 8px 28px rgba(0,0,0,0.08);
        }}
        .logo {{
            text-align: center;
            margin-bottom: 25px;
        }}
        .logo img {{
            width: 160px;
            opacity: 0.98;
        }}
        h2 {{
            text-align: center;
            font-size: 26px;
            font-weight: 700;
            margin-bottom: 18px;
            color: #0F422F;
        }}
        p {{
            font-size: 15px;
            line-height: 1.55;
            margin-bottom: 14px;
            color: #394248;
        }}
        .code-box {{
            font-size: 32px;
            font-weight: 700;
            background: #F6FAF9;
            padding: 18px;
            border-radius: 12px;
            text-align: center;
            color: #1A4D45;
            letter-spacing: 7px;
            margin: 28px auto;
            width: 70%;
            border: 1px solid #DCE7E4;
        }}
        a.button {{
            display: inline-block;
            padding: 14px 26px;
            background: #F9C66A;
            color: #1A1A1A !important;
            font-weight: 600;
            text-decoration: none;
            border-radius: 10px;
            margin-top: 25px;
            font-size: 15px;
            border: 1px solid #E3B058;
        }}
        a.button:hover {{
            background: #E8B75F;
        }}
        .center {{
            text-align: center;
        }}
        .footer {{
            margin-top: 40px;
            font-size: 12px;
            color: #6A737B;
            text-align: center;
            border-top: 1px solid #E2E8F0;
            padding-top: 18px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- LOGO -->
        <div class="logo">
            <img src="cid:logo" alt="UniRide Logo">
        </div>

        <p>{message}</p>

        {middle_html}

        <p class="center" style="margin-top: 18px; font-weight: 600;">
            {finalmessage}
        </p>

        <!-- FOOTER -->
        <p class="footer">
            © UniRide 2026 — Movilidad inteligente para campus universitarios.
        </p>
    </div>
</body>
</html>"""

    text_content = strip_tags(message.replace('<br>', '\n')) + "\n\n" + middle_text + "\n\n" + strip_tags(finalmessage.replace('<br>', '\n'))

    email_msg = EmailMultiAlternatives(subject, text_content, from_email, [email])
    email_msg.attach_alternative(html_content, "text/html")

    logo_path = Path(settings.BASE_DIR) / "email_assets" / "logo-uniride2.png"
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            logo = MIMEImage(f.read())
            logo.add_header("Content-ID", "<logo>")
            logo.add_header("Content-Disposition", "inline", filename="logo.png")
            email_msg.attach(logo)

    email_msg.send()

from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from email.mime.image import MIMEImage
from pathlib import Path
import os


def send_suspension_email(user, complaints, suspension):
    subject = "Estado de tu cuenta - UniRide"
    from_email = settings.DEFAULT_FROM_EMAIL

    # ========================
    # TEXTO PLANO
    # ========================
    complaints_text = "\n".join(
        f"- {c.type_id.name}: {c.description}" for c in complaints
    ) or "- No se especificaron quejas."

    if suspension.is_permanent:
        text_content = f"""
Hola {user.name},

Tu cuenta ha sido BLOQUEADA PERMANENTEMENTE.

Motivos:
{complaints_text}

Comentario del administrador:
{suspension.reason}

Esta suspensión es definitiva.
"""
    else:
        text_content = f"""
Hola {user.name},

Tu cuenta ha sido suspendida temporalmente.

Motivos:
{complaints_text}

Comentario del administrador:
{suspension.reason}

Podrás volver a acceder el:
{suspension.end_date.strftime('%d/%m/%Y')}
"""

    # ========================
    # HTML – QUEJAS
    # ========================
    complaints_html = "".join(
        f"""
        <li style="margin-bottom:6px;">
            <strong>{c.type_id.name}:</strong> {c.description}
        </li>
        """
        for c in complaints
    ) or "<li>No se especificaron quejas.</li>"

    # ========================
    # ESTADO
    # ========================
    if suspension.is_permanent:
        status_title = "Cuenta Bloqueada"
        status_color = "#b91c1c"
        status_message = "Tu cuenta ha sido bloqueada permanentemente."
        extra_info = "<strong>Esta suspensión es definitiva.</strong>"
    else:
        status_title = "Cuenta Suspendida"
        status_color = "#f59e0b"
        status_message = "Tu cuenta ha sido suspendida temporalmente."
        extra_info = f"""
        Podrás volver a acceder a UniRide el:
        <strong>{suspension.end_date.strftime('%d/%m/%Y')}</strong>
        """

    # ========================
    # HTML FINAL
    # ========================
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background-color: #f8f9fa; padding: 20px;">
        <div style="max-width:520px;margin:auto;background:white;border-radius:12px;padding:30px;">
          <div style="text-align:center;margin-bottom:20px;">
            <img src="cid:logo" alt="UniRide" style="height:60px;" />
          </div>

          <h2 style="color:{status_color};text-align:center;">
            {status_title}
          </h2>

          <p>Hola <strong>{user.name}</strong>,</p>
          <p>{status_message}</p>

          <ul>{complaints_html}</ul>

          <p><strong>Comentario del administrador:</strong><br>{suspension.reason}</p>

          <p>{extra_info}</p>

          <p style="font-size:12px;color:#999;text-align:center;">
            UniRide © 2026
          </p>
        </div>
      </body>
    </html>
    """

    email_message = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=from_email,
        to=[user.email],
    )

    email_message.attach_alternative(html_content, "text/html")

    logo_path = Path(settings.BASE_DIR) / "email_assets" / "logo-uniride2.png"

    if logo_path.exists():
        with open(logo_path, "rb") as f:
            logo = MIMEImage(f.read())
            logo.add_header("Content-ID", "<logo>")
            logo.add_header("Content-Disposition", "inline", filename="logo.png")
            email_message.attach(logo)

    email_message.send()
