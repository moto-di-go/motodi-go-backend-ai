from datetime import UTC, date, datetime, time
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _normalize_text(value: str) -> str:
    return " ".join(value.strip().split())


class AnnouncementCandidate(BaseModel):
    id: str = Field(min_length=1)
    departure_city: str = Field(min_length=1)
    destination_city: str = Field(min_length=1)
    departure_quarter: str | None = None
    departure_date: date | None = None
    departure_time: time | None = None
    price_fcfa: Decimal | None = Field(default=None, ge=0)
    remaining_seats: int = Field(ge=0)
    total_seats: int | None = Field(default=None, ge=1)
    transporter_rating: float | None = Field(default=None, ge=0, le=5)
    status: str = "PUBLISHED"

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("departure_city", "destination_city", "departure_quarter", mode="before")
    @classmethod
    def normalize_strings(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _normalize_text(value)


class RecommendationRequest(BaseModel):
    departure_city: str = Field(min_length=1)
    destination_city: str = Field(min_length=1)
    quarter: str | None = None
    preferred_time_start: time | None = None
    preferred_time_end: time | None = None
    departure_date: date | None = None
    requested_seats: int = Field(default=1, ge=1, le=20)
    max_price_fcfa: Decimal | None = Field(default=None, ge=0)
    anonymized_user_context: str | None = Field(default=None, max_length=256)
    candidate_announcements: list[AnnouncementCandidate] = Field(default_factory=list)

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("departure_city", "destination_city", "quarter", mode="before")
    @classmethod
    def normalize_strings(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _normalize_text(value)

    @field_validator("preferred_time_end")
    @classmethod
    def validate_time_range(cls, value: time | None, info: object) -> time | None:
        data = getattr(info, "data", {})
        start = data.get("preferred_time_start")
        if start is not None and value is not None and value <= start:
            msg = "preferred_time_end must be after preferred_time_start"
            raise ValueError(msg)
        return value


class RecommendationItem(BaseModel):
    announcement_id: str
    score: Annotated[float, Field(ge=0, le=1)]
    reason: str
    fallback: bool = False
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class RecommendationResponse(BaseModel):
    recommendations: list[RecommendationItem]
    fallback: bool
    message: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    latency_ms: float = Field(ge=0)
