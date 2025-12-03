from app.models.location import Location, Place

# NOTE: These are illustrative coordinates in Addis Ababa; replace/extend with real data.
SAMPLE_PLACES: list[Place] = [
    Place(
        id="1",
        name="Piassa Cafe",
        category="cafe",
        location=Location(lat=9.0320, lng=38.7530),
        district="Arada",
        sub_city="Piassa",
    ),
    Place(
        id="2",
        name="Bole Mall",
        category="shopping",
        location=Location(lat=8.9945, lng=38.7890),
        district="Bole",
        sub_city="Bole",
    ),
    Place(
        id="3",
        name="Meskel Square",
        category="landmark",
        location=Location(lat=9.0108, lng=38.7613),
        district="Kirkos",
        sub_city="Meskel",
    ),
]


