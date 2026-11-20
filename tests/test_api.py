from unittest.mock import patch

from fastapi.testclient import TestClient

from dpdpcompass.api.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ready():
    with patch("dpdpcompass.api.routes.health.SessionLocal") as mock_session_local:
        mock_session = mock_session_local.return_value.__enter__.return_value

        response = client.get("/ready")

        assert response.status_code == 200
        assert response.json() == {
            "status": "ready",
            "checks": {"database": True},
        }
        mock_session.execute.assert_called_once()


def test_ready_database_failure():
    from sqlalchemy.exc import SQLAlchemyError

    with patch("dpdpcompass.api.routes.health.SessionLocal") as mock_session_local:
        mock_session = mock_session_local.return_value.__enter__.return_value
        mock_session.execute.side_effect = SQLAlchemyError("database unavailable")

        response = client.get("/ready")

        assert response.status_code == 503
        assert response.json() == {
            "status": "not_ready",
            "checks": {"database": False},
        }
