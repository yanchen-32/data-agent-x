from fastapi.testclient import TestClient

from dataagentx.main import app

client = TestClient(app)


def test_health_status_code() -> None:
    response = client.get("/health")
    assert response.status_code == 200


def test_health_body() -> None:
    response = client.get("/health")
    assert response.json() == {"status": "ok"}