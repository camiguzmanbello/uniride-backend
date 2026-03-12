# Guía de Despliegue en Render para UniRide API

Esta guía te ayudará a desplegar tu proyecto Django en Render.com paso a paso.

## 1. Preparación del Proyecto

El proyecto ya ha sido configurado con los archivos necesarios para el despliegue:

*   **`requirements.txt`**: Lista de dependencias actualizada (incluye `gunicorn`, `dj-database-url`, `whitenoise`).
*   **`render.yaml`**: Archivo de configuración "Blueprint" para Render (define la base de datos y el servicio web).
*   **`build.sh`**: Script de construcción que instala dependencias, recopila archivos estáticos, aplica migraciones y **crea un superusuario automáticamente**.
*   **`UniRide/settings/production.py`**: Configuración específica para producción.

## 2. Crear una cuenta en Render

Si no tienes una cuenta, regístrate en [https://render.com/](https://render.com/).

## 3. Conectar con GitHub/GitLab

1.  Sube tu código a un repositorio en GitHub o GitLab si aún no lo has hecho.
2.  En el dashboard de Render, haz clic en **New +** y selecciona **Blueprint**.
3.  Conecta tu cuenta de GitHub/GitLab y selecciona el repositorio de `UniRide`.

## 4. Configuración del Blueprint

Render detectará automáticamente el archivo `render.yaml`.

1.  Verás que se crearán dos servicios:
    *   `uniride_db`: Una base de datos PostgreSQL.
    *   `uniride-api`: El servicio web de tu aplicación.
2.  **IMPORTANTE**: Render te pedirá valores para las variables de entorno definidas en `render.yaml`. Debes rellenar:
    *   `DJANGO_SUPERUSER_EMAIL`: El correo para tu usuario administrador (ej. `admin@uniride.com`).
    *   `DJANGO_SUPERUSER_PASSWORD`: La contraseña para tu usuario administrador.
    *   `DJANGO_SUPERUSER_NAME`: (Opcional, por defecto "Admin")
    *   `DJANGO_SUPERUSER_PHONE`: (Opcional, por defecto "0000000000")
3.  Haz clic en **Apply**.

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

> **Nota:** `DATABASE_URL` y `SECRET_KEY` se generan automáticamente gracias al `render.yaml`.

## 6. Despliegue

Una vez que hayas aplicado el Blueprint y configurado las variables, Render comenzará el proceso.

1.  Clonará el repositorio.
2.  Ejecutará `./build.sh`. Esto incluirá:
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
