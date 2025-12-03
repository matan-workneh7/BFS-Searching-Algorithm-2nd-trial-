from pydantic import BaseModel


class CityBoundary(BaseModel):
    name: str
    min_lat: float
    max_lat: float
    min_lng: float
    max_lng: float


class Settings(BaseModel):
    city_name: str = "Addis Ababa"
    # Simple bounding box for Addis Ababa (approximate; can be refined)
    boundary: CityBoundary = CityBoundary(
        name="Addis Ababa",
        min_lat=8.8,
        max_lat=9.1,
        min_lng=38.6,
        max_lng=38.9,
    )


settings = Settings()


