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
        mock_session.scalar.return_value = 20

        response = client.get("/ready")

        assert response.status_code == 200
        assert response.json() == {
            "status": "ready",
            "checks": {"database": True},
            "records_count": 20,
        }
        mock_session.execute.assert_called_once()


def test_ready_not_enough_records():
    with patch("dpdpcompass.api.routes.health.SessionLocal") as mock_session_local:
        mock_session = mock_session_local.return_value.__enter__.return_value
        mock_session.scalar.return_value = 19

        response = client.get("/ready")

        assert response.status_code == 503
        assert response.json() == {
            "status": "not_ready",
            "checks": {"database": True},
            "records_count": 19,
        }


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
            "records_count": 0,
        }


def test_document_stats():
    response = client.get("/v1/documents/stats")

    assert response.status_code == 200
    assert response.json() == {
        "total": 20,
        "by_source": {
            "Government of India": 1,
            "India Code": 12,
            "MeitY": 7,
        },
    }
