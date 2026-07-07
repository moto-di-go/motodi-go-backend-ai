import re
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

RAW_EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
RAW_PHONE_PATTERN = re.compile(r"(\+?237)?\s?6\d(?:[\s.-]?\d){7}\b")


class AiEventType(StrEnum):
    CALL = "call"
    CLICK = "click"
    ACCEPTED = "accepted"
    ERROR = "error"


class AiEventRequest(BaseModel):
    event_type: AiEventType
    latency_ms: float | None = Field(default=None, ge=0)
    fallback: bool = False
    recommendation_count: int | None = Field(default=None, ge=0)
    anonymized_user_context: str | None = Field(default=None, max_length=256)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("anonymized_user_context")
    @classmethod
    def reject_raw_context(cls, value: str | None) -> str | None:
        if value and _contains_raw_personal_data(value):
            msg = "anonymized_user_context must not contain raw phone numbers or emails"
            raise ValueError(msg)
        return value

    @model_validator(mode="after")
    def reject_raw_metadata(self) -> "AiEventRequest":
        if _contains_raw_personal_data(self.metadata):
            msg = "metadata must not contain raw phone numbers or emails"
            raise ValueError(msg)
        return self


class AiEventResponse(BaseModel):
    accepted: bool
    event_type: AiEventType
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AiMetricsResponse(BaseModel):
    call_count: int
    accepted_suggestion_count: int
    acceptance_rate: float
    average_latency_ms: float
    error_count: int
    fallback_count: int
    period_start: datetime | None = None
    period_end: datetime | None = None


def _contains_raw_personal_data(value: object) -> bool:
    if isinstance(value, str):
        return bool(RAW_EMAIL_PATTERN.search(value) or RAW_PHONE_PATTERN.search(value))
    if isinstance(value, dict):
        return any(_contains_raw_personal_data(item) for item in value.values())
    if isinstance(value, list | tuple | set):
        return any(_contains_raw_personal_data(item) for item in value)
    return False
