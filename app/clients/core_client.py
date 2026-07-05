import httpx

from app.config import Settings
from app.schemas.recommendations import AnnouncementCandidate, RecommendationRequest


class BackendCoreClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def fetch_announcements(
        self,
        request: RecommendationRequest,
    ) -> list[AnnouncementCandidate]:
        params: dict[str, str | int] = {
            "departureCity": request.departure_city,
            "destinationCity": request.destination_city,
            "requestedSeats": request.requested_seats,
            "onlyAvailable": "true",
        }
        if request.quarter:
            params["quarter"] = request.quarter
        if request.departure_date:
            params["date"] = request.departure_date.isoformat()
        if request.max_price_fcfa is not None:
            params["maxPrice"] = str(request.max_price_fcfa)

        url = f"{self._settings.backend_core_base_url.rstrip('/')}/api/v1/intercity/announcements"
        try:
            async with httpx.AsyncClient(timeout=self._settings.request_timeout_seconds) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
        except httpx.HTTPError:
            return []

        payload = response.json()
        raw_items = _extract_items(payload)
        candidates: list[AnnouncementCandidate] = []
        for item in raw_items:
            try:
                candidates.append(AnnouncementCandidate.model_validate(_to_candidate_payload(item)))
            except ValueError:
                continue
        return candidates


def _extract_items(payload: object) -> list[object]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("items", "content", "announcements", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
    return []


def _to_candidate_payload(item: object) -> dict[str, object]:
    if not isinstance(item, dict):
        return {}
    return {
        "id": item.get("id") or item.get("announcementId"),
        "departure_city": item.get("departure_city") or item.get("departureCity"),
        "destination_city": item.get("destination_city") or item.get("destinationCity"),
        "departure_quarter": item.get("departure_quarter") or item.get("departureQuarter"),
        "departure_date": item.get("departure_date") or item.get("departureDate"),
        "departure_time": item.get("departure_time") or item.get("departureTime"),
        "price_fcfa": item.get("price_fcfa") or item.get("priceFcfa") or item.get("price"),
        "remaining_seats": item.get("remaining_seats") or item.get("remainingSeats") or 0,
        "total_seats": item.get("total_seats") or item.get("totalSeats"),
        "transporter_rating": item.get("transporter_rating") or item.get("transporterRating"),
        "status": item.get("status") or "PUBLISHED",
    }
