
import os
from pathlib import Path
try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv()


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

try:
    from decouple import config as env_config
except Exception:
    def env_config(key, default=None):
        if key in os.environ:
            return os.environ[key]
        if default is not None:
            return default
        raise KeyError(key)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env_config('SECRET_KEY')



# Application definition

INSTALLED_APPS = [
    'corsheaders',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'apps.chat',
    'apps.users',
    'apps.complaints',
    'apps.core',
    'apps.ratings',
    'apps.trips',
    'apps.notifications',
    'apps.match',
    'drf_yasg',
    'cloudinary',
    'cloudinary_storage',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware', 
    'django.middleware.common.CommonMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'apps.core.middleware.ForzarIdiomaMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'UniRide.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                "django.template.context_processors.debug",
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'UniRide.wsgi.application'

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

# POLITICA DE CONTRASEÑAS 
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', #Evita que un usuario cree una contraseña demasiado parecida a su propio
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', #Establece una longitud mínima de la contraseña.
        'OPTIONS': {'min_length': 8},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', #Rechaza contraseñas comunes o fácilmente adivinables.
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', #Evita que la contraseña esté compuesta solo de números.
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'es'

TIME_ZONE = 'America/Bogota'

USE_I18N = True

USE_TZ = True


AUTH_USER_MODEL = 'users.User'

# Configuración de autenticación de DRF
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'apps.users.authentication.CookieJWTAuthentication',  # Para cada request, valida el usuario usando la cookie access_token
    ),
}

# Tiempo de expiración y comportamiento del JWT
from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15), 
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),     
    "ROTATE_REFRESH_TOKENS": True,  # genera nuevo refresh_token al usarlo
    "BLACKLIST_AFTER_ROTATION": True,  # invalida el anterior
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
}
AUTHENTICATION_BACKENDS = [
    'apps.users.backends.EmailBackend',  
    'django.contrib.auth.backends.ModelBackend',  
]
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': 'Formato esperado: Bearer <tu_token_jwt>',
        }
    },
    'USE_SESSION_AUTH': False,
}

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = env_config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env_config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env_config('DEFAULT_FROM_EMAIL', default=EMAIL_HOST_USER)

FRONTEND_URL = env_config('FRONTEND_URL', default='https://app.unirideweb.online')
PASSWORD_RESET_PATH = env_config('PASSWORD_RESET_PATH', default='/confirm-reset-password')

LOGIN_PAYLOAD_PRIVATE_KEY_PEM = env_config('LOGIN_PAYLOAD_PRIVATE_KEY_PEM', default='')
LOGIN_PAYLOAD_PUBLIC_KEY_PEM = env_config('LOGIN_PAYLOAD_PUBLIC_KEY_PEM', default='')

# Usar Cloudinary para archivos de media
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
STATICFILES_STORAGE = 'cloudinary_storage.storage.StaticHashedCloudinaryStorage'

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': os.environ.get('CLOUDINARY_API_KEY'),
    'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET'),
    'secure': True,
}

DEFAULT_PROFILE_IMAGE = "https://res.cloudinary.com/dzgcubnp2/image/upload/v1765315248/placeholder-user_h1zyal.png"
