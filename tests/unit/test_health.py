from fastapi.testclient import TestClient

from dpdpcompass.api.deps import get_document_repository
from dpdpcompass.api.main import app


def test_health():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_includes_version():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["version"] == "dev"


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


def test_list_documents_search_no_result(fake_repo):
    app.dependency_overrides[get_document_repository] = lambda: fake_repo

    try:
        client = TestClient(app)

        response = client.get("/v1/documents?q=nonexistent")

        assert response.status_code == 200
        assert response.json() == []
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


def test_list_documents_multiple_metadata_filters(fake_repo):
    app.dependency_overrides[get_document_repository] = lambda: fake_repo

    try:
        client = TestClient(app)

        response = client.get("/v1/documents?year=2023&source=India%20Code")

        assert response.status_code == 200

        documents = response.json()

        assert len(documents) == 1
        assert documents[0]["title"] == "DPDP Act 2023"
    finally:
        app.dependency_overrides.clear()


def test_list_documents_source_filter(fake_repo):
    app.dependency_overrides[get_document_repository] = lambda: fake_repo

    try:
        client = TestClient(app)

        response = client.get("/v1/documents?source=India%20Code")

        assert response.status_code == 200
        assert len(response.json()) == 1
    finally:
        app.dependency_overrides.clear()


def test_list_documents_document_type_filter(fake_repo):
    app.dependency_overrides[get_document_repository] = lambda: fake_repo

    try:
        client = TestClient(app)

        response = client.get("/v1/documents?document_type=act")

        assert response.status_code == 200
        assert len(response.json()) == 1
    finally:
        app.dependency_overrides.clear()


def test_list_documents_invalid_year_filter(fake_repo):
    app.dependency_overrides[get_document_repository] = lambda: fake_repo

    try:
        client = TestClient(app)

        response = client.get("/v1/documents?year=abc")

        assert response.status_code == 400
        assert response.json()["detail"] == ("Metadata filter 'year' must be an integer.")
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


def test_list_documents_limit(fake_repo):
    app.dependency_overrides[get_document_repository] = lambda: fake_repo

    try:
        client = TestClient(app)

        response = client.get("/v1/documents?limit=1")

        assert response.status_code == 200

        documents = response.json()

        assert len(documents) == 1
    finally:
        app.dependency_overrides.clear()


def test_list_documents_invalid_limit(fake_repo):
    app.dependency_overrides[get_document_repository] = lambda: fake_repo

    try:
        client = TestClient(app)

        response = client.get("/v1/documents?limit=0")

        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_get_document_found(fake_repo):
    app.dependency_overrides[get_document_repository] = lambda: fake_repo

    try:
        client = TestClient(app)

        response = client.get("/v1/documents/1")

        assert response.status_code == 200
        assert response.json()["title"] == "DPDP Act 2023"
    finally:
        app.dependency_overrides.clear()


def test_get_document_not_found(fake_repo):
    app.dependency_overrides[get_document_repository] = lambda: fake_repo

    try:
        client = TestClient(app)

        response = client.get("/v1/documents/999")

        assert response.status_code == 404
        assert "was not found" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()
