from unittest.mock import patch

from fastapi.testclient import TestClient

from dpdpcompass.api.deps import get_document_repository
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


def test_document_page():
    fake_repo = type(
        "FakeRepo",
        (),
        {
            "get_page": lambda self, external_id, page_no: {
                "id": external_id,
                "page_no": page_no,
                "text": "DPDP Act page text",
                "headings": ["Chapter 1", "Definitions"],
            }
        },
    )()

    app.dependency_overrides[get_document_repository] = lambda: fake_repo
    try:
        response = client.get("/v1/documents/1/pages?page_no=1")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "1"
    assert data["page_no"] == 1
    assert data["text"] == "DPDP Act page text"
    assert data["headings"] == ["Chapter 1", "Definitions"]


def test_document_page_not_found():
    fake_repo = type(
        "FakeRepo",
        (),
        {"get_page": lambda self, external_id, page_no: None},
    )()

    app.dependency_overrides[get_document_repository] = lambda: fake_repo
    try:
        response = client.get("/v1/documents/1/pages?page_no=999")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    data = response.json()
    assert data["status"] == 404
    assert "Page '999' for document '1' was not found." in data["detail"]
