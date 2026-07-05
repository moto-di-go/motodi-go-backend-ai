from dataclasses import dataclass
from datetime import UTC, datetime
from threading import Lock

from app.schemas.metrics import AiEventRequest, AiEventType, AiMetricsResponse


@dataclass(frozen=True)
class StoredAiEvent:
    event_type: AiEventType
    recorded_at: datetime
    latency_ms: float | None
    fallback: bool
    recommendation_count: int | None


class AiMetricsService:
    def __init__(self) -> None:
        self._events: list[StoredAiEvent] = []
        self._lock = Lock()

    def record(self, request: AiEventRequest) -> StoredAiEvent:
        event = StoredAiEvent(
            event_type=request.event_type,
            recorded_at=datetime.now(UTC),
            latency_ms=request.latency_ms,
            fallback=request.fallback,
            recommendation_count=request.recommendation_count,
        )
        with self._lock:
            self._events.append(event)
        return event

    def summarize(
        self,
        period_start: datetime | None = None,
        period_end: datetime | None = None,
    ) -> AiMetricsResponse:
        events = self._filtered_events(period_start, period_end)
        call_count = sum(1 for event in events if event.event_type == AiEventType.CALL)
        accepted_count = sum(1 for event in events if event.event_type == AiEventType.ACCEPTED)
        error_count = sum(1 for event in events if event.event_type == AiEventType.ERROR)
        fallback_count = sum(1 for event in events if event.fallback)
        latencies = [event.latency_ms for event in events if event.latency_ms is not None]
        average_latency = sum(latencies) / len(latencies) if latencies else 0.0
        acceptance_rate = accepted_count / call_count if call_count else 0.0
        return AiMetricsResponse(
            call_count=call_count,
            accepted_suggestion_count=accepted_count,
            acceptance_rate=round(acceptance_rate, 4),
            average_latency_ms=round(average_latency, 2),
            error_count=error_count,
            fallback_count=fallback_count,
            period_start=period_start,
            period_end=period_end,
        )

    def clear(self) -> None:
        with self._lock:
            self._events.clear()

    def _filtered_events(
        self,
        period_start: datetime | None,
        period_end: datetime | None,
    ) -> list[StoredAiEvent]:
        with self._lock:
            events = list(self._events)
        if period_start is not None:
            events = [event for event in events if event.recorded_at >= period_start]
        if period_end is not None:
            events = [event for event in events if event.recorded_at <= period_end]
        return events


metrics_service = AiMetricsService()
