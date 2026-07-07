from time import perf_counter
from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.clients.core_client import BackendCoreClient
from app.config import Settings, get_settings
from app.schemas.metrics import AiEventRequest, AiEventType
from app.schemas.recommendations import RecommendationRequest, RecommendationResponse
from app.services.metrics import metrics_service
from app.services.recommendations import RecommendationService

router = APIRouter(prefix="/api/v1/ai", tags=["recommendations"])


SettingsDependency = Annotated[Settings, Depends(get_settings)]


def get_recommendation_service(settings: SettingsDependency) -> RecommendationService:
    return RecommendationService(settings=settings, core_client=BackendCoreClient(settings))


RecommendationServiceDependency = Annotated[
    RecommendationService,
    Depends(get_recommendation_service),
]


@router.post("/recommendations", response_model=RecommendationResponse)
async def recommend(
    payload: RecommendationRequest,
    request: Request,
    service: RecommendationServiceDependency,
) -> RecommendationResponse:
    started_at = perf_counter()
    recommendations, fallback, message = await service.recommend(payload)
    latency_ms = (perf_counter() - started_at) * 1000
    metrics_service.record(
        AiEventRequest(
            event_type=AiEventType.CALL,
            latency_ms=latency_ms,
            fallback=fallback,
            recommendation_count=len(recommendations),
            anonymized_user_context=payload.anonymized_user_context,
            metadata={"path": request.url.path},
        )
    )
    return RecommendationResponse(
        recommendations=recommendations,
        fallback=fallback,
        message=message,
        latency_ms=round(latency_ms, 2),
    )
