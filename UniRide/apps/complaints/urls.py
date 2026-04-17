from django.urls import path
from rest_framework.routers import DefaultRouter

# Importaciones explícitas (SIN *)
from .views import (
    list_active_complaints,
    resolve_complaint,
    get_interactable_users,
    create_complaint,
    get_complaint_types,
    create_complaint_type,
    get_complaint_status,
    create_complaint_status
)

# Router (si en el futuro usas ViewSets)
router = DefaultRouter()

urlpatterns = [
    # ==============================
    # ENDPOINTS ADMINISTRADOR
    # ==============================
    path(
        'admin/active/',
        list_active_complaints,
        name='list_active_complaints'
    ),
    path(
        'admin/<int:complaint_id>/resolve/',
        resolve_complaint,
        name='resolve_complaint'
    ),

    # ==============================
    # ENDPOINTS USUARIO
    # ==============================
    path(
        'interactable-users/',
        get_interactable_users,
        name='get_interactable_users'
    ),
    path(
        'create/',
        create_complaint,
        name='create_complaint'
    ),

    # ==============================
    # ADMIN - CONFIGURACIÓN
    # ==============================
    # Complaint Types
    path('types/', get_complaint_types, name='get_complaint_types'),
    path('types/create/', create_complaint_type, name='create_complaint_type'),

    # Complaint Status
    path('statuses/', get_complaint_status, name='get_complaint_status'),
    path('statuses/create/', create_complaint_status, name='create_complaint_status'),
]

# Si luego usas ViewSets, puedes hacer:
urlpatterns += router.urls