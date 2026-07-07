from fastapi.testclient import TestClient


def _payload() -> dict[str, object]:
    return {
        "departure_city": "Douala",
        "destination_city": "Yaounde",
        "quarter": "Bonamoussadi",
        "preferred_time_start": "06:00:00",
        "preferred_time_end": "09:00:00",
        "requested_seats": 1,
        "max_price_fcfa": 10000,
        "candidate_announcements": [
            {
                "id": "ann-low",
                "departure_city": "Douala",
                "destination_city": "Yaounde",
                "departure_quarter": "Akwa",
                "departure_time": "12:30:00",
                "price_fcfa": 12000,
                "remaining_seats": 1,
                "transporter_rating": 3.8,
            },
            {
                "id": "ann-best",
                "departure_city": "Douala",
                "destination_city": "Yaounde",
                "departure_quarter": "Bonamoussadi",
                "departure_time": "07:30:00",
                "price_fcfa": 9000,
                "remaining_seats": 3,
                "transporter_rating": 4.6,
            },
        ],
    }


def test_recommendations_are_sorted_by_score(client: TestClient) -> None:
    response = client.post("/api/v1/ai/recommendations", json=_payload())

    assert response.status_code == 200
    body = response.json()
    recommendations = body["recommendations"]
    assert body["fallback"] is False
    assert recommendations[0]["announcement_id"] == "ann-best"
    assert recommendations[0]["score"] >= recommendations[1]["score"]
    assert "reason" in recommendations[0]
    assert "Prix dans budget" in recommendations[0]["reason"]


def test_recommendations_fallback_when_no_candidate(client: TestClient) -> None:
    response = client.post(
        "/api/v1/ai/recommendations",
        json={
            "departure_city": "Douala",
            "destination_city": "Yaounde",
            "requested_seats": 1,
            "candidate_announcements": [],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["recommendations"] == []
    assert body["fallback"] is True
    assert "Aucune annonce compatible" in body["message"]


def test_backend_core_unavailable_uses_empty_fallback(client: TestClient) -> None:
    response = client.post(
        "/api/v1/ai/recommendations",
        json={
            "departure_city": "Douala",
            "destination_city": "Yaounde",
            "requested_seats": 1,
        },
    )

    assert response.status_code == 200
    assert response.json()["fallback"] is True


def test_request_validation_rejects_invalid_seats(client: TestClient) -> None:
    payload = _payload()
    payload["requested_seats"] = 0

    response = client.post("/api/v1/ai/recommendations", json=payload)

    assert response.status_code == 422

