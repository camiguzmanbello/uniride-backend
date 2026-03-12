from apps.ratings.models import Rating
from django.db.models import Avg


def calculate_score(distance_km, time_diff_min, route_deviation_km, driver_rating):

    MAX_DISTANCE = 2
    MAX_TIME = 45
    MAX_DETOUR = 15

    distance_score = max(0, 1 - (distance_km / MAX_DISTANCE))
    time_score = max(0, 1 - (time_diff_min / MAX_TIME))
    route_score = max(0, 1 - (route_deviation_km / MAX_DETOUR))
    rating_score = driver_rating / 5

    score = (
        distance_score * 0.35 +
        time_score * 0.25 +
        route_score * 0.25 +
        rating_score * 0.15
    )

    return round(score, 3)

def driver_rating_score(driver):
    """
    Calcula el promedio de estrellas recibidas
    por el usuario conductor.
    """

    avg = (
        Rating.objects
        .filter(reviewed_id=driver)
        .aggregate(avg=Avg("stars"))
        ["avg"]
    )

    if avg is None:
        return 0.5  # rating neutro si no tiene calificaciones

    return avg / 5
