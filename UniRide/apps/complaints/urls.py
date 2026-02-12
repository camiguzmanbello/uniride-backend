from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import * 

router = DefaultRouter() 
urlpatterns = [
    # Endpoints para Administradores
    path(
        'admin/active/',
        list_active_complaints
    ),
    path(
        'admin/<int:complaint_id>/resolve/',
        resolve_complaint
    ),
    # Endpoints para Usuarios
    path(
        'interactable-users/',
        get_interactable_users
    ),
    path(
        'create/',
        create_complaint
    ),
    # Gestión de Tipos y Estados (Admin)
    path(
        'types/',
        manage_complaint_types
    ),
    path(
        'statuses/',
        manage_complaint_status
    ),
]
