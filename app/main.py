from fastapi import FastAPI

from app.config import get_settings
from app.routers import metrics, recommendations


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="MOTO'DI GO intercity AI recommendation microservice.",
    )
    app.include_router(recommendations.router)
    app.include_router(metrics.router)

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {
            "status": "ok",
            "service": settings.app_name,
            "environment": settings.environment,
        }

    return app


app = create_app()

