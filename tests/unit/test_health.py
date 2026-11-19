from fastapi.testclient import TestClient

from dpdpcompass.api.deps import get_document_repository
from dpdpcompass.api.main import app


def test_health():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_list_documents_with_fake_repository(fake_repo):
    app.dependency_overrides[get_document_repository] = lambda: fake_repo

    try:
        client = TestClient(app)

        response = client.get("/v1/documents")

        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["title"] == "DPDP Act 2023"
    finally:
        app.dependency_overrides.clear()
