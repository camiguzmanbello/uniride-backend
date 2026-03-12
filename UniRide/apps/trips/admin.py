from django.contrib import admin
from .models import Publication, PublicationType, Trip, TripStatus, TripPassenger, TripPassengerStatus

@admin.register(PublicationType)
class PublicationTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(TripStatus)
class TripStatusAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(TripPassengerStatus)
class TripPassengerStatusAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = ('type_id', 'user_id', 'departure_place', 'destination', 'departure_datetime', 'is_active')
    search_fields = ('user_id__email', 'departure_place', 'destination')
    list_filter = ('type_id', 'is_active')

@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ('driver_id', 'status_id', 'created_at', 'finalized_at')
    search_fields = ('driver_id__email',)
    list_filter = ('status_id', 'auto_finalized')

@admin.register(TripPassenger)
class TripPassengerAdmin(admin.ModelAdmin):
    list_display = ('passenger_id', 'trip_id', 'status_id', 'joined_at', 'seats_reserved')
    search_fields = ('passenger_id__email',)
    list_filter = ('status_id',)
