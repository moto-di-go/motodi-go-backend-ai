from datetime import UTC, datetime

from app.clients.core_client import BackendCoreClient
from app.config import Settings
from app.schemas.recommendations import (
    AnnouncementCandidate,
    RecommendationItem,
    RecommendationRequest,
)
from app.services.scoring import build_reason, score_announcement


class RecommendationService:
    def __init__(self, settings: Settings, core_client: BackendCoreClient) -> None:
        self._settings = settings
        self._core_client = core_client

    async def recommend(
        self,
        request: RecommendationRequest,
    ) -> tuple[list[RecommendationItem], bool, str]:
        candidates = list(request.candidate_announcements)
        fallback = False

        if not candidates:
            candidates = await self._core_client.fetch_announcements(request)
            fallback = not candidates

        recommendations = self._rank_candidates(request, candidates, fallback=fallback)
        if not recommendations:
            return [], True, "Aucune annonce compatible disponible pour ces criteres."

        message = "Recommandations calculees avec le scoring deterministe initial."
        if fallback:
            message = "Backend core indisponible ou sans donnees; fallback deterministe applique."
        return recommendations, fallback, message

    def _rank_candidates(
        self,
        request: RecommendationRequest,
        candidates: list[AnnouncementCandidate],
        fallback: bool,
    ) -> list[RecommendationItem]:
        generated_at = datetime.now(UTC)
        scored: list[RecommendationItem] = []
        for candidate in candidates:
            score, reasons = score_announcement(request, candidate)
            if score <= 0:
                continue
            scored.append(
                RecommendationItem(
                    announcement_id=candidate.id,
                    score=score,
                    reason=build_reason(reasons),
                    fallback=fallback,
                    generated_at=generated_at,
                )
            )

        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[: self._settings.max_recommendations]
