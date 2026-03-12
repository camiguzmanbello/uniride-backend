from itsdangerous import URLSafeTimedSerializer
from django.conf import settings

def generate_reset_token(email):
    serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
    return serializer.dumps(email, salt='password-reset-salt')

def verify_reset_token(token, expiration=600):  # 10 minutos por defecto
    serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=expiration)
        return email
    except Exception:
        return None
