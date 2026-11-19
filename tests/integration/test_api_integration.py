from fastapi.testclient import TestClient

from dpdpcompass.api.main import app


def test_health_integration():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
