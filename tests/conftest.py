import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.metrics import metrics_service


@pytest.fixture(autouse=True)
def clear_metrics() -> None:
    metrics_service.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)

