import pytest
from fastapi.testclient import TestClient

from dataagentx.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_create_item_returns_201(client: TestClient) -> None:
    response = client.post("/items", json={"name": "book"})
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "book"
    assert isinstance(body["id"], int)


def test_create_item_rejects_empty_name(client: TestClient) -> None:
    response = client.post("/items", json={"name": ""})
    assert response.status_code == 422


def test_get_missing_item_returns_404(client: TestClient) -> None:
    response = client.get("/items/999999")
    assert response.status_code == 404