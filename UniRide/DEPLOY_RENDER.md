# Guía de Despliegue en Render para UniRide API

Esta guía te ayudará a desplegar tu proyecto Django en Render.com paso a paso.

## 1. Preparación del Proyecto

El proyecto ya ha sido configurado con los archivos necesarios para el despliegue:

*   **`requirements.txt`**: Lista de dependencias actualizada (incluye `gunicorn`, `dj-database-url`, `whitenoise`).
*   **`render.yaml`**: Archivo de configuración para Render (define la base de datos y el servicio web).
*   **`build.sh`**: Script de construcción que instala dependencias, recopila archivos estáticos, aplica migraciones y **crea un superusuario automáticamente**.
*   **`UniRide/settings/production.py`**: Configuración específica para producción.

## 2. Crear una cuenta en Render

Si no tienes una cuenta, regístrate en [https://render.com/](https://render.com/).

## 3. Conectar con GitHub/GitLab

1.  Sube tu código a un repositorio en GitHub o GitLab si aún no lo has hecho.
2.  Conecta tu cuenta de GitHub/GitLab y selecciona el repositorio.

## 4. Configuración en Render

Este repo tiene el proyecto Django dentro de la carpeta `UniRide/`. Por eso en Render debes elegir una de estas opciones:

1.  **Configurar Root Directory = `UniRide` en el servicio** (recomendado si ya creaste el servicio).
2.  **Mover `render.yaml` al root del repo** si quieres usar Render Blueprints (el archivo debe estar en la raíz del repositorio para que Render lo detecte automáticamente).

Si estás creando el servicio manualmente, usa estos valores:

*   **Root Directory**: `UniRide`
*   **Build Command**: `bash ./build.sh`
*   **Start Command**: `gunicorn UniRide.wsgi:application --bind 0.0.0.0:$PORT --workers $WEB_CONCURRENCY --timeout 120`

## 5. Variables de Entorno Adicionales

Además de las anteriores, necesitas agregar manualmente las credenciales de Cloudinary y email en el dashboard de Render.

Ve a la sección **Environment** de tu servicio web (`uniride-api`) y agrega:

| Clave | Valor |
| :--- | :--- |
| `CLOUDINARY_CLOUD_NAME` | Tu Cloud Name de Cloudinary |
| `CLOUDINARY_API_KEY` | Tu API Key de Cloudinary |
| `CLOUDINARY_API_SECRET` | Tu API Secret de Cloudinary |
| `EMAIL_HOST_USER` | (Opcional) Tu correo para envío de emails |
| `EMAIL_HOST_PASSWORD` | (Opcional) Tu contraseña de aplicación para emails |
| `PYTHON_VERSION` | Versión de Python (recomendado fijar una estable, ej. `3.12.9`) |
| `CORS_ALLOWED_ORIGINS` | URLs del frontend separadas por coma (sin espacios) |
| `CSRF_TRUSTED_ORIGINS` | URLs del frontend separadas por coma (sin espacios) |
| `CORS_ALLOWED_ORIGIN_REGEXES` | (Opcional) Regex para permitir subdominios variables |

> **Nota:** `DATABASE_URL` y `SECRET_KEY` se generan automáticamente gracias al `render.yaml`.
>
> **Importante (CORS/CSRF):** en `UniRide/settings/base.py` hay valores de `localhost` para desarrollo. En producción (`UniRide/settings/production.py`) se toman desde estas variables de entorno.
>
> Ejemplo:
>
> - `CORS_ALLOWED_ORIGINS`: `https://tu-frontend.onrender.com,https://tudominio.com`
> - `CSRF_TRUSTED_ORIGINS`: `https://tu-frontend.onrender.com,https://tudominio.com`
>
> Si estás usando despliegues preview en Vercel (dominios que cambian), puedes usar:
>
> - `CORS_ALLOWED_ORIGIN_REGEXES`: `^https://uniride-front.*\\.vercel\\.app$`

## 6. Despliegue

Una vez que hayas configurado el servicio y las variables, Render comenzará el proceso.

1.  Clonará el repositorio.
2.  Ejecutará `bash ./build.sh`. Esto incluirá:
    *   `pip install ...`
    *   `collectstatic`
    *   `migrate`
    *   **`ensure_superuser`**: Creará tu usuario administrador si no existe.
3.  Iniciará el servidor.

Puedes ver el progreso en la pestaña **Logs**.

## 7. Verificación

Cuando el despliegue finalice, Render te proporcionará una URL (ej. `https://uniride-api.onrender.com`).

Visita esa URL y prueba acceder a `/admin` con las credenciales que configuraste (`DJANGO_SUPERUSER_EMAIL` y `DJANGO_SUPERUSER_PASSWORD`).

## Solución de Problemas Comunes

*   **Error de Base de Datos**: Asegúrate de que el servicio de base de datos (`uniride_db`) esté activo y vinculado correctamente.
*   **Archivos Estáticos**: Si los estilos no cargan, verifica los logs del paso `collectstatic`. WhiteNoise está configurado para servirlos.
*   **Allowed Hosts**: Si ves un error "DisallowedHost", asegúrate de que `ALLOWED_HOSTS` en `production.py` incluya tu dominio de Render (o `['*']`).
