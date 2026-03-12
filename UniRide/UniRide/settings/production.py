from .base import *
import dj_database_url
import os

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['*']  # En producción, esto debería ser tu dominio de Render

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///' + str(BASE_DIR / 'db.sqlite3'),
        conn_max_age=600
    )
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

# Configuración de WhiteNoise para servir archivos estáticos
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Asegurarse de que CSRF confíe en el dominio de Render
CSRF_TRUSTED_ORIGINS = ['https://*.onrender.com']

csrf_trusted_origins_env = os.environ.get('CSRF_TRUSTED_ORIGINS', '').strip()
if csrf_trusted_origins_env:
    for origin in [o.strip() for o in csrf_trusted_origins_env.split(',') if o.strip()]:
        if origin not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(origin)

cors_allowed_origins_env = os.environ.get('CORS_ALLOWED_ORIGINS', '').strip()
if cors_allowed_origins_env:
    CORS_ALLOWED_ORIGINS = [o.strip() for o in cors_allowed_origins_env.split(',') if o.strip()]
else:
    CORS_ALLOWED_ORIGINS = []
