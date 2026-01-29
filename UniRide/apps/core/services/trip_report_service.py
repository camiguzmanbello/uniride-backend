# core/services/trip_report_service.py

from django.db.models import QuerySet
from apps.trips.models import Trip
from apps.core.utils.reportsFilters import apply_date_status_filters 
def get_trip_report_queryset(request) -> QuerySet:
    """
    Devuelve el queryset base de viajes con todos los filtros aplicados.
    Usado tanto para preview como para PDF.
    """
    trips = (
        Trip.objects
        .select_related(
            "driver_id",
            "status_id",
            "publication_id",
        )
        .prefetch_related(
            "passengers__passenger_id",
            "passengers__status_id",
        )
    )

    trips = apply_date_status_filters(
        trips,
        request,
        date_field="publication_id__departure_datetime"
    )

    return trips
