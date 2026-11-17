def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready(client):
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["records"] == 5


def test_list_documents(client):
    response = client.get("/v1/documents?limit=5")

    assert response.status_code == 200
    assert len(response.json()) == 5


def test_get_document(client):
    response = client.get("/v1/documents/001")

    assert response.status_code == 200
    assert response.json()["title"] == "Digital Personal Data Protection Act, 2023"


def test_document_not_found(client):
    response = client.get("/v1/documents/999")

    assert response.status_code == 404
    assert response.json()["status"] == 404
    assert response.headers["content-type"].startswith("application/problem+json")


def test_invalid_limit(client):
    response = client.get("/v1/documents?limit=0")

    assert response.status_code == 422
