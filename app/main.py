from fastapi import FastAPI

from app.api.routes import router as api_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Addis Ababa Recommendation System",
        description="API for city-wide recommendations in Addis Ababa.",
        version="0.1.0",
    )

    # Register API routes
    app.include_router(api_router, prefix="/api")

    return app


app = create_app()


