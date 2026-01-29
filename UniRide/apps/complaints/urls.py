from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import * 

router = DefaultRouter() 
urlpatterns = [
    path(
        'complaints/admin/active/',
        list_active_complaints
    ),
    path(
        'complaints/admin/<int:complaint_id>/resolve/',
        resolve_complaint
    ),
]
