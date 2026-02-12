from utils.geo_utils import haversine_distance
from match.models import Route
def get_closest_route(lat, lon):
    """
    Dada una coordenada (lat, lon),
    retorna la ruta más cercana según sus puntos.

    Usado para:
    - pasajeros (ej: Bojacá)
    - conductores
    """

    closest_route = None
    min_distance = float('inf')

    for route in Route.objects.filter(is_active=True):
        for point in route.points.all():
            distance = haversine_distance(
                lat, lon,
                point.latitude, point.longitude
            )

            if distance < min_distance:
                min_distance = distance
                closest_route = route

    return closest_route

def get_closest_point_on_route(route, lat, lon):
    """
    Retorna el punto de una ruta
    más cercano a una coordenada.
    """

    closest_point = None
    min_distance = float('inf')

    for point in route.points.all():
        distance = haversine_distance(
            lat, lon,
            point.latitude, point.longitude
        )

        if distance < min_distance:
            min_distance = distance
            closest_point = point

    return closest_point

def assign_route_to_publication(publication):
    """
    Asigna internamente una ruta lógica
    a una publicación (driver o passenger).

    No visible para el usuario.
    """

    route = get_closest_route(
        publication.lat_departure_place,
        publication.lon_departure_place
    )

    publication.route_info.route = route
    publication.route_info.save()

    return route

def are_on_same_route(pub_a, pub_b):
    """
    Verifica si dos publicaciones
    pertenecen a la misma ruta lógica.
    """
    return (
        pub_a.route_info.route_id ==
        pub_b.route_info.route_id
    )

def is_direction_compatible(driver_pub, passenger_pub):
    """
    Verifica si el sentido del viaje es compatible.
    Municipio → Universidad o viceversa.
    """

    return (
        driver_pub.route_info.direction ==
        passenger_pub.route_info.direction
    )
