from apps.trips.models import Publication
from apps.match.models import MatchSuggestion
from .time_service import is_time_compatible
from .score_service import calculate_score, driver_rating_score
from apps.match.utils.geo_utils import haversine_distance

def generate_suggestions_for_driver(driver_publication):
    """
    Genera sugerencias de pasajeros para un conductor.
    """
    passengers = Publication.objects.filter(
        is_active=True,
        type_id=2
    )

    for passenger in passengers:
        # 1️⃣ Horario
        if not is_time_compatible(
            driver_publication.departure_datetime,
            passenger.departure_datetime
        ):
            continue

        # 2️⃣ Cupos
        if driver_publication.available_seats <= 0:
            continue

        # 3️⃣ Ruta lógica
        if driver_publication.route_info.route_id != passenger.route_info.route_id:
            continue

        # 4️⃣ Distancia
        distance = haversine_distance(
            passenger.lat_departure_place,
            passenger.lon_departure_place,
            driver_publication.lat_departure_place,
            driver_publication.lon_departure_place
        )

        # 5️⃣ Score
        score = calculate_score(
            distance_km=distance,
            time_diff_min=10,
            driver_rating=driver_rating_score(driver_publication.user_id)
        )

        MatchSuggestion.objects.get_or_create(
            driver_publication=driver_publication,
            passenger_publication=passenger,
            defaults={'score': score}
        )
