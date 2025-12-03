import math

from app.core.config import settings
from app.models.location import Location


def haversine_distance_meters(a: Location, b: Location) -> float:
    """
    Compute great-circle distance between two points (meters).
    """
    r = 6371000  # Earth radius in meters
    lat1, lon1, lat2, lon2 = map(math.radians, [a.lat, a.lng, b.lat, b.lng])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    h = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    return 2 * r * math.asin(math.sqrt(h))


def is_within_addis(location: Location) -> bool:
    """
    Check if a location lies within the configured Addis Ababa boundary.
    """
    boundary = settings.boundary
    return (
        boundary.min_lat <= location.lat <= boundary.max_lat
        and boundary.min_lng <= location.lng <= boundary.max_lng
    )


