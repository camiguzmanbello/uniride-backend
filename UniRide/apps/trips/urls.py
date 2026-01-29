from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import * 

router = DefaultRouter()
router.register(r'publication-types', PublicationTypeViewSet, basename='publication-types')
router.register(r'publications', PublicationViewSet, basename='publications')
router.register(r'trippassengers', TripPassengerViewSet, basename='trippassenger')
router.register(r'trip-statuses', TripStatusViewSet, basename='trip-statuses')
router.register(r'trip-passenger-statuses', TripPassengerStatusViewSet, basename='trip-passenger-statuses')
router.register(r'trips', TripViewSet, basename='trips')



urlpatterns = [
    path('', include(router.urls)),
]