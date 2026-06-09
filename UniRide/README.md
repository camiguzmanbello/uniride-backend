# UniRide Backend

## Descripción

UniRide es una plataforma de movilidad colaborativa diseñada para conectar conductores y pasajeros dentro de la comunidad universitaria de forma segura y eficiente.

Este repositorio contiene el backend de la aplicación, desarrollado con Django y Django REST Framework, proporcionando una arquitectura API REST para la gestión de usuarios, viajes, autenticación, calificaciones, quejas y procesos administrativos.

### Mi contribución principal

* Desarrollo completo del panel administrativo.
* Implementación del sistema de autenticación basado en JWT.
* Desarrollo del sistema de auditoría y gestión de usuarios.
* Diseño e implementación del sistema de emparejamiento inteligente entre conductores y pasajeros.
* Implementación de lógica de validación y seguridad de la plataforma.
* Desarrollo y documentación de APIs REST.

## Tecnologías usadas

* Python
* Django
* Django REST Framework
* MySQL
* JWT Authentication
* Swagger/OpenAPI
* Git & GitHub
* Scrum

## Cómo correrlo localmente

### Clonar el repositorio

```bash
git clone https://github.com/camiguzmanbello/uniride-backend.git
```

### Crear entorno virtual

```bash
python -m venv env
```

### Activar entorno virtual

Windows:

```bash
env\Scripts\activate
```

### Instalar dependencias

```bash
pip install -r requirements.txt
```

### Ejecutar migraciones

```bash
python manage.py migrate
```

### Ejecutar servidor

```bash
python manage.py runserver
```

## Screenshots / Demo

* Panel administrativo
* Gestión de usuarios
* Gestión de viajes
* Sistema de auditoría
* Documentación Swagger

## Estado del proyecto

Proyecto académico funcional con despliegue y mejoras continuas.
