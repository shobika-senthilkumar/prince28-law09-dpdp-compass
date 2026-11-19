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

        documents = response.json()

        assert isinstance(documents, list)
        assert len(documents) == 1
        assert documents[0]["title"] == "DPDP Act 2023"
    finally:
        app.dependency_overrides.clear()


def test_list_documents_search(fake_repo):
    app.dependency_overrides[get_document_repository] = lambda: fake_repo

    try:
        client = TestClient(app)

        response = client.get("/v1/documents?q=DPDP")

        assert response.status_code == 200

        documents = response.json()

        assert len(documents) == 1
        assert documents[0]["title"] == "DPDP Act 2023"
    finally:
        app.dependency_overrides.clear()


def test_list_documents_metadata_filter(fake_repo):
    app.dependency_overrides[get_document_repository] = lambda: fake_repo

    try:
        client = TestClient(app)

        response = client.get("/v1/documents?year=2023")

        assert response.status_code == 200

        documents = response.json()

        assert len(documents) == 1
        assert documents[0]["year"] == 2023
    finally:
        app.dependency_overrides.clear()


def test_list_documents_invalid_filter(fake_repo):
    app.dependency_overrides[get_document_repository] = lambda: fake_repo

    try:
        client = TestClient(app)

        response = client.get("/v1/documents?invalid_filter=test")

        assert response.status_code == 400
    finally:
        app.dependency_overrides.clear()
