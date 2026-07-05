from datetime import datetime

from fastapi import APIRouter

from app.schemas.metrics import AiEventRequest, AiEventResponse, AiMetricsResponse
from app.services.metrics import metrics_service

router = APIRouter(prefix="/api/v1/ai", tags=["metrics"])


@router.post("/events", response_model=AiEventResponse)
async def record_event(payload: AiEventRequest) -> AiEventResponse:
    event = metrics_service.record(payload)
    return AiEventResponse(
        accepted=True,
        event_type=event.event_type,
        recorded_at=event.recorded_at,
    )


@router.get("/metrics", response_model=AiMetricsResponse)
async def get_metrics(
    period_start: datetime | None = None,
    period_end: datetime | None = None,
) -> AiMetricsResponse:
    return metrics_service.summarize(period_start=period_start, period_end=period_end)
