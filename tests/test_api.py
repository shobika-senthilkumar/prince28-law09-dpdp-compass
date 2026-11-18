def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready(client):
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["checks"]["database"] is True


def test_list_documents(client):
    response = client.get("/v1/documents?limit=5")

    assert response.status_code == 200
    assert len(response.json()) == 5


def test_get_document(client):
    response = client.get("/v1/documents/001")

    assert response.status_code == 200
    assert response.json()["title"] == "Digital Personal Data Protection Act, 2023"


def test_filter_documents_by_source(client):
    response = client.get(
        "/v1/documents?metadata_source=India%20Code",
    )

    assert response.status_code == 200
    documents = response.json()

    assert len(documents) > 0
    assert all(document["metadata"]["source"] == "India Code" for document in documents)


def test_filter_documents_by_year(client):
    response = client.get("/v1/documents?metadata_year=2023")

    assert response.status_code == 200
    documents = response.json()

    assert len(documents) > 0
    assert all(document["metadata"]["year"] == 2023 for document in documents)


def test_filter_documents_by_document_type(client):
    response = client.get("/v1/documents?metadata_document_type=Act")

    assert response.status_code == 200
    documents = response.json()

    assert len(documents) > 0
    assert all(document["metadata"]["document_type"] == "Act" for document in documents)


def test_document_not_found(client):
    response = client.get("/v1/documents/999")

    assert response.status_code == 404
    assert response.json()["status"] == 404
    assert response.headers["content-type"].startswith("application/problem+json")


def test_invalid_limit(client):
    response = client.get("/v1/documents?limit=0")

    assert response.status_code == 422


def test_get_missing_document(client):
    response = client.get("/v1/documents/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Document '999' was not found."


def test_search_documents(client):
    response = client.get("/v1/documents?q=Digital%20Personal%20Data")

    assert response.status_code == 200
    documents = response.json()

    assert len(documents) > 0
    assert any("Digital Personal Data" in document["title"] for document in documents)


def test_invalid_metadata_filter(client):
    response = client.get("/v1/documents?invalid_filter=test")

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid metadata filter: 'invalid_filter'"


def test_direct_source_metadata_filter(client):
    response = client.get("/v1/documents?source=India%20Code")

    assert response.status_code == 200
    documents = response.json()

    assert len(documents) > 0
    assert all(document["metadata"]["source"] == "India Code" for document in documents)


def test_direct_year_metadata_filter(client):
    response = client.get("/v1/documents?year=2023")

    assert response.status_code == 200
    documents = response.json()

    assert len(documents) > 0
    assert all(document["metadata"]["year"] == 2023 for document in documents)


def test_direct_document_type_metadata_filter(client):
    response = client.get("/v1/documents?document_type=Act")

    assert response.status_code == 200
    documents = response.json()

    assert len(documents) > 0
    assert all(document["metadata"]["document_type"] == "Act" for document in documents)


def test_search_documents_by_description(client):
    response = client.get("/v1/documents?q=personal%20data")

    assert response.status_code == 200
    documents = response.json()

    assert len(documents) > 0
