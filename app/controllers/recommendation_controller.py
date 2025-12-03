from app.schemas.recommendation import RecommendationResponse
from app.services.recommendation_service import RecommendationService

service = RecommendationService()


def get_recommendations(
    lat: float,
    lng: float,
    category: str | None,
    limit: int,
) -> list[RecommendationResponse]:
    return service.get_recommendations(lat=lat, lng=lng, category=category, limit=limit)


