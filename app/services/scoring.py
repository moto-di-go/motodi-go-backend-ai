from datetime import time
from decimal import Decimal
from unicodedata import normalize

from app.schemas.recommendations import AnnouncementCandidate, RecommendationRequest


def score_announcement(
    request: RecommendationRequest,
    announcement: AnnouncementCandidate,
) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []

    if _same_text(request.departure_city, announcement.departure_city):
        score += 0.25
    else:
        return 0.0, ["Ville de depart non compatible"]

    if _same_text(request.destination_city, announcement.destination_city):
        score += 0.25
    else:
        return 0.0, ["Ville de destination non compatible"]

    if announcement.remaining_seats >= request.requested_seats:
        score += 0.2
        reasons.append(f"{announcement.remaining_seats} places restantes")
    else:
        return 0.0, ["Places insuffisantes"]

    if request.quarter and announcement.departure_quarter:
        if _same_text(request.quarter, announcement.departure_quarter):
            score += 0.1
            reasons.append("Depart proche")
    elif request.quarter is None:
        score += 0.05

    if _price_matches(request.max_price_fcfa, announcement.price_fcfa):
        score += 0.08
        reasons.append("Prix dans budget")

    if _time_matches(request, announcement.departure_time):
        score += 0.08
        reasons.append("Horaire compatible")

    seat_bonus = min(announcement.remaining_seats, 5) * 0.008
    score += seat_bonus

    if announcement.transporter_rating is not None and announcement.transporter_rating >= 4:
        score += 0.02
        reasons.append("Transporteur bien note")

    if not reasons:
        reasons.append("Annonce compatible")

    return min(round(score, 4), 1.0), reasons


def build_reason(reasons: list[str]) -> str:
    selected = reasons[:3]
    return ", ".join(selected)


def _same_text(left: str, right: str) -> bool:
    return _fold(left) == _fold(right)


def _fold(value: str) -> str:
    folded = normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return " ".join(folded.casefold().strip().split())


def _time_matches(request: RecommendationRequest, departure_time: time | None) -> bool:
    if request.preferred_time_start is None and request.preferred_time_end is None:
        return True
    if departure_time is None:
        return False
    if request.preferred_time_start is not None and departure_time < request.preferred_time_start:
        return False
    return not (
        request.preferred_time_end is not None and departure_time > request.preferred_time_end
    )


def _price_matches(max_price: Decimal | None, price: Decimal | None) -> bool:
    if max_price is None:
        return True
    if price is None:
        return False
    return price <= max_price
