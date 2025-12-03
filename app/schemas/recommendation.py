from pydantic import BaseModel, Field


class LocationPoint(BaseModel):
    lat: float = Field(..., description="Latitude in decimal degrees")
    lng: float = Field(..., description="Longitude in decimal degrees")


class RecommendationResponse(BaseModel):
    id: str
    name: str
    category: str
    location: LocationPoint
    district: str | None = None
    sub_city: str | None = None
    distance_meters: float | None = Field(
        default=None, description="Approximate distance from requested point"
    )


