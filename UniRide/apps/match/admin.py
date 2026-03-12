from django.contrib import admin
from .models import Route, RoutePoint, PublicationRoute, MatchSuggestion

@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ('name', 'direction')

@admin.register(RoutePoint)
class RoutePointAdmin(admin.ModelAdmin):
    list_display = ('route', 'name', 'order', 'latitude', 'longitude')

@admin.register(PublicationRoute)
class PublicationRouteAdmin(admin.ModelAdmin):
    list_display = ('publication', 'route', 'closest_point')

@admin.register(MatchSuggestion)
class MatchSuggestionAdmin(admin.ModelAdmin):
    list_display = ('driver_publication', 'passenger_publication', 'score', 'is_active', 'created_at')
