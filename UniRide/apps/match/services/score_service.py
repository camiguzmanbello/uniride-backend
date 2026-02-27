from apps.ratings.models import Rating
from django.db.models import Avg


def calculate_score(distance_km, time_diff_min, driver_rating):
    """
    Calcula el score total de compatibilidad.
    Retorna un valor entre 0 y 1.
    """
    distance_score = max(0, 1 - (distance_km / 5))
    time_score = max(0, 1 - (time_diff_min / 30))
    rating_score = driver_rating / 5

    return (
        distance_score * 0.4 +
        time_score * 0.3 +
        rating_score * 0.3
    )

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
