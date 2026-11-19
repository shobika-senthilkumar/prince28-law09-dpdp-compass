from fastapi.testclient import TestClient

from dpdpcompass.api.main import app


def test_health_integration():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_list_documents_integration():
    client = TestClient(app)

    response = client.get("/v1/documents")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_documents_with_search_integration():
    client = TestClient(app)

    response = client.get("/v1/documents?q=DPDP")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_documents_with_source_filter_integration():
    client = TestClient(app)

    response = client.get("/v1/documents?source=India%20Code")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_documents_with_year_filter_integration():
    client = TestClient(app)

    response = client.get("/v1/documents?year=2023")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_documents_with_document_type_filter_integration():
    client = TestClient(app)

    response = client.get("/v1/documents?document_type=act")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_document_integration():
    client = TestClient(app)

    response = client.get("/v1/documents/1")

    assert response.status_code in {200, 404}
