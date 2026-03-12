from apps.match.services.route_service import are_on_same_route, is_direction_compatible
from apps.trips.models import Publication
from apps.match.models import MatchSuggestion
from .time_service import is_time_compatible
from .score_service import calculate_score, driver_rating_score
from apps.match.utils.geo_utils import haversine_distance

MAX_PICKUP_DISTANCE = 3
MAX_ROUTE_DEVIATION = 15


def generate_suggestions_for_driver(driver_publication):

    passengers = Publication.objects.filter(
        is_active=True,
        type_id=1,
    )

    for passenger in passengers:

        # evitar mismo usuario
        if passenger.user_id == driver_publication.user_id:
            continue

        # horario compatible
        if not is_time_compatible(
            driver_publication.departure_datetime,
            passenger.departure_datetime
        ):
            continue

        # cupos
        if driver_publication.available_seats <= 0:
            continue

        # misma ruta
        if not are_on_same_route(driver_publication, passenger):
            continue

        # misma direccion
        if not is_direction_compatible(driver_publication, passenger):
            continue


        # distancia directa conductor - pasajero
        distance = haversine_distance(
            passenger.lat_departure_place,
            passenger.lon_departure_place,
            driver_publication.lat_departure_place,
            driver_publication.lon_departure_place
        )


        # desviación dentro de la ruta
        route_deviation = haversine_distance(
            passenger.route_info.closest_point.latitude,
            passenger.route_info.closest_point.longitude,
            driver_publication.route_info.closest_point.latitude,
            driver_publication.route_info.closest_point.longitude
        )


        # si la desviación es absurda
        if route_deviation > MAX_ROUTE_DEVIATION:
            continue


        # diferencia de tiempo
        time_diff = abs(
            driver_publication.departure_datetime -
            passenger.departure_datetime
        ).total_seconds() / 60


        score = calculate_score(
            distance_km=distance,
            time_diff_min=time_diff,
            route_deviation_km=route_deviation,
            driver_rating=driver_rating_score(driver_publication.user_id)
        )


        MatchSuggestion.objects.get_or_create(
            driver_publication=driver_publication,
            passenger_publication=passenger,
            defaults={"score": score}
        )