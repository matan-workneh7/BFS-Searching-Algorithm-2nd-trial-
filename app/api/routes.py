from fastapi import APIRouter

from app.controllers import recommendation_controller


router = APIRouter()


@router.get("/health", tags=["system"])
def health_check():
    return {"status": "ok"}


@router.get("/recommendations", tags=["recommendations"])
def get_recommendations(
    lat: float,
    lng: float,
    category: str | None = None,
    limit: int = 10,
):
    """
    Get recommendations for any location within Addis Ababa.
    """
    return recommendation_controller.get_recommendations(
        lat=lat,
        lng=lng,
        category=category,
        limit=limit,
    )


