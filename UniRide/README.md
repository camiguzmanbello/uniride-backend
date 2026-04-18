# UniRide API (Django + DRF)

Backend de UniRide basado en Django REST Framework.

## Requisitos

- Python 3.12+ (recomendado)
- PostgreSQL (para entorno local por defecto)

## Estructura rápida

- La raíz del proyecto es la carpeta donde está `manage.py`.
- `manage.py` usa por defecto `DJANGO_SETTINGS_MODULE=UniRide.settings.local`.

## Configuración (.env)

Crea un archivo `.env` en la raíz (junto a `manage.py`) con lo mínimo para arrancar:

- `SECRET_KEY=...`

Opcionales (según lo que vayas a probar):

- Base de datos (si no usas los valores por defecto del settings local):
  - `POSTGRES_DB=uniride_db`
  - `POSTGRES_USER=uniride_user`
  - `POSTGRES_PASSWORD=1234`
  - `POSTGRES_HOST=localhost`
  - `POSTGRES_PORT=5432`
- CORS/hosts:
  - `ALLOWED_HOSTS=127.0.0.1,localhost`
  - `DEBUG=true`
- Emails (recuperación de contraseña):
  - `EMAIL_HOST_USER=...`
  - `EMAIL_HOST_PASSWORD=...`
  - `DEFAULT_FROM_EMAIL=...`
  - `FRONTEND_URL=https://app.unirideweb.online`
  - `PASSWORD_RESET_PATH=/confirm-reset-password`
- Cloudinary (si vas a subir imágenes/archivos):
  - `CLOUDINARY_CLOUD_NAME=...`
  - `CLOUDINARY_API_KEY=...`
  - `CLOUDINARY_API_SECRET=...`
- Login con payload cifrado (opcional):
  - `LOGIN_PAYLOAD_PRIVATE_KEY_PEM=...`
  - `LOGIN_PAYLOAD_PUBLIC_KEY_PEM=...`

## Instalación

Desde la raíz del proyecto (donde está `manage.py`):

1) Crear y activar entorno virtual

- Windows (PowerShell):
  - `python -m venv .venv`
  - `.venv\Scripts\Activate.ps1`
- Linux/Mac:
  - `python3 -m venv .venv`
  - `source .venv/bin/activate`

2) Instalar dependencias

- Actualizar pip:
  - `python -m pip install --upgrade pip`
- Instalar dependencias del proyecto:
  - `python -m pip install -r requirements.txt`

Si falla la instalación de paquetes con componentes nativos (por ejemplo `pycairo`), instala primero las herramientas de compilación de C++ para tu sistema y vuelve a ejecutar el comando.

## Base de datos (PostgreSQL)

El entorno local (`UniRide.settings.local`) usa PostgreSQL. Asegúrate de tener el servicio corriendo y una base creada.

Si usas los valores por defecto del settings local, crea:

- Base de datos: `uniride_db`
- Usuario: `uniride_user`
- Password: `1234`

## Migraciones y servidor

1) Aplicar migraciones:

- `python manage.py migrate`

2) (Opcional) Crear superusuario para `/admin`:

- Interactivo:
  - `python manage.py createsuperuser`
- No interactivo (si defines variables de entorno):
  - `DJANGO_SUPERUSER_EMAIL=...`
  - `DJANGO_SUPERUSER_PASSWORD=...`
  - y luego:
  - `python manage.py ensure_superuser`

3) Levantar el servidor:

- `python manage.py runserver`

Por defecto quedará en:

- `http://127.0.0.1:8000/`

## Documentación de la API

- Swagger UI: `http://127.0.0.1:8000/swagger/`
- Redoc: `http://127.0.0.1:8000/redoc/`

## Login con payload cifrado (opcional)

El endpoint de login soporta un payload cifrado con RSA-OAEP(SHA-256) + AES-256-GCM. Si quieres probar esa modalidad:

1) Genera llaves RSA (muestra PEMs y variables de entorno):

- `python manage.py generate_login_rsa_keys`

2) Copia las variables `LOGIN_PAYLOAD_PRIVATE_KEY_PEM` y `LOGIN_PAYLOAD_PUBLIC_KEY_PEM` a tu `.env`.

## Exportación a TXT (DNDA)

En esta raíz hay scripts para exportar todos los `.py` a `.txt` manteniendo estructura y generar un ZIP final:

- Ejecutar (doble clic): `export_py_to_txt.bat`
- Salida:
  - Carpeta: `dnda_txt_export/`
  - ZIP: `dnda_txt_export.zip`

## Producción / Render

Hay una guía específica en [DEPLOY_RENDER.md](file:///c:/Users/kevin_r/OneDrive/Escritorio/UniRide_API/UniRide/DEPLOY_RENDER.md).
