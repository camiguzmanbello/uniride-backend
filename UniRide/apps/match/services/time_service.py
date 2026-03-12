from datetime import timedelta

TIME_WINDOW_MINUTES = 45

def is_time_compatible(driver_time, passenger_time):
    """
    Verifica si dos horarios están dentro
    de una ventana de tolerancia.
    """
    diff = abs(driver_time - passenger_time)
    return diff <= timedelta(minutes=TIME_WINDOW_MINUTES)
