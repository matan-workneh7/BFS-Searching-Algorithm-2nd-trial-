from typing import Iterable

from app.models.location import Location, Place
from app.repositories.place_repository import InMemoryPlaceRepository
from app.schemas.recommendation import LocationPoint, RecommendationResponse
from app.utils.geo import haversine_distance_meters, is_within_addis


class RecommendationService:
    """
    Core business logic for generating recommendations anywhere in Addis Ababa.
    """

    def __init__(self) -> None:
        self._places_repo = InMemoryPlaceRepository()

    def get_recommendations(
        self,
        lat: float,
        lng: float,
        category: str | None,
        limit: int,
    ) -> list[RecommendationResponse]:
        user_location = Location(lat=lat, lng=lng)

        if not is_within_addis(user_location):
            # In a real system you might still respond but clamp or redirect.
            # Here we simply return an empty list to indicate out-of-bound requests.
            return []

        places = self._places_repo.list_places()
        filtered = self._filter_places(places, category)
        ranked = self._rank_by_distance(filtered, user_location)

        return [
            RecommendationResponse(
                id=place.id,
                name=place.name,
                category=place.category,
                location=LocationPoint(lat=place.location.lat, lng=place.location.lng),
                district=place.district,
                sub_city=place.sub_city,
                distance_meters=distance,
            )
            for place, distance in ranked[:limit]
        ]

    def _filter_places(
        self, places: Iterable[Place], category: str | None
    ) -> list[Place]:
        if category is None:
            return list(places)
        category_lower = category.lower()
        return [p for p in places if p.category.lower() == category_lower]

    def _rank_by_distance(
        self, places: Iterable[Place], origin: Location
    ) -> list[tuple[Place, float]]:
        ranked: list[tuple[Place, float]] = []
        for place in places:
            distance = haversine_distance_meters(origin, place.location)
            ranked.append((place, distance))

        ranked.sort(key=lambda item: item[1])
        return ranked


