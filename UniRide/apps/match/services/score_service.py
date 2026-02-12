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
    Normaliza el rating del conductor.
    """
    if not driver.rating:
        return 0.5
    return driver.rating / 5

def driver_rating_score(driver):
    """
    Normaliza el rating del conductor.
    """
    if not driver.rating:
        return 0.5
    return driver.rating / 5
