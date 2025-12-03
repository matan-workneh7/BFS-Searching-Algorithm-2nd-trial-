from dataclasses import dataclass


@dataclass(frozen=True)
class Location:
    """
    Represents a geographic point in Addis Ababa.
    """

    lat: float
    lng: float


@dataclass
class Place:
    """
    Represents a place that can be recommended.
    """

    id: str
    name: str
    category: str
    location: Location
    district: str | None = None
    sub_city: str | None = None


