from django.utils import timezone
import random
from apps.users.models import PendingUser
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

def generate_verification_code():
    """Genera un código único de 6 dígitos no expirado."""
    while True:
        code = str(random.randint(100000, 999999))
        if not PendingUser.objects.filter(code=code, expires_at__gt=timezone.now()).exists():
            return code

def send_code_email(subject: str, message: str, code: str, finalmessage: str, email: str) -> None:

    from_email = settings.DEFAULT_FROM_EMAIL
    
    # Cuerpo de texto plano (por compatibilidad con clientes antiguos)
    text_content = message

    # Cuerpo HTML con estilos inline
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background-color: #f8f9fa; padding: 20px;">
        <div style="max-width: 500px; margin: auto; background-color: white; border-radius: 10px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
          <h2 style="color: #0c4a6e; text-align: center;">Verificación de Cuenta</h2>
          <p style="font-size: 16px; color: #333;">{message}</p>
          <div style="text-align: center; margin: 20px 0;">
            <span style="display: inline-block; padding: 10px 20px; font-size: 24px; background-color: #0c4a6e; color: white; border-radius: 8px; letter-spacing: 2px;">
              {code}
            </span>
          </div>         
          <p style="font-size: 14px; color: #666;">{finalmessage}</p>
          <p style="font-size: 14px; color: #999; text-align: center; margin-top: 30px;">Uniride © 2025</p>
        </div>
      </body>
    </html>
    """

    # Crear el objeto de correo
    email_msg = EmailMultiAlternatives(subject, text_content, from_email, [email])
    email_msg.attach_alternative(html_content, "text/html")
    email_msg.send()