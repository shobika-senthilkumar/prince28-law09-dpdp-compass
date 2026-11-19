from unittest.mock import patch

from fastapi.testclient import TestClient

from dpdpcompass.api.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ready():
    with patch("dpdpcompass.api.routes.health.engine") as mock_engine:
        mock_connection = mock_engine.connect.return_value.__enter__.return_value
        mock_connection.execute.return_value = None

        response = client.get("/ready")

        assert response.status_code == 200
        assert response.json()["status"] == "ready"
        assert response.json()["checks"]["database"] is True


def test_ready_database_failure():
    from sqlalchemy.exc import SQLAlchemyError

    with patch("dpdpcompass.api.routes.health.engine") as mock_engine:
        mock_engine.connect.side_effect = SQLAlchemyError("Database unavailable")

        response = client.get("/ready")

        assert response.status_code == 503
        assert response.json()["status"] == "not_ready"
        assert response.json()["checks"]["database"] is False
