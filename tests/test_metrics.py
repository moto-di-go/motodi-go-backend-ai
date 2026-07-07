from fastapi.testclient import TestClient


def test_metrics_aggregate_calls_and_acceptance(client: TestClient) -> None:
    call_response = client.post(
        "/api/v1/ai/events",
        json={
            "event_type": "call",
            "latency_ms": 120,
            "fallback": True,
            "recommendation_count": 2,
            "anonymized_user_context": "hash:user-segment-regular",
        },
    )
    accepted_response = client.post(
        "/api/v1/ai/events",
        json={"event_type": "accepted", "latency_ms": 80},
    )

    response = client.get("/api/v1/ai/metrics")

    assert call_response.status_code == 200
    assert accepted_response.status_code == 200
    assert response.status_code == 200
    body = response.json()
    assert body["call_count"] == 1
    assert body["accepted_suggestion_count"] == 1
    assert body["acceptance_rate"] == 1
    assert body["average_latency_ms"] == 100
    assert body["fallback_count"] == 1


def test_metrics_reject_raw_email_in_metadata(client: TestClient) -> None:
    response = client.post(
        "/api/v1/ai/events",
        json={
            "event_type": "click",
            "metadata": {"email": "aline.ngo@example.cm"},
        },
    )

    assert response.status_code == 422


def test_metrics_reject_raw_cameroon_phone_in_context(client: TestClient) -> None:
    response = client.post(
        "/api/v1/ai/events",
        json={
            "event_type": "call",
            "anonymized_user_context": "+237699001122",
        },
    )

    assert response.status_code == 422

