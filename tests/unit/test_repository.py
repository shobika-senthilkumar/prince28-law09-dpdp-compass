from unittest.mock import MagicMock

from dpdpcompass.db.repository import DocumentRepository


def make_document():
    document = MagicMock()
    document.external_id = "DOC001"
    document.title = "DPDP Act 2023"
    document.source = "India Code"
    document.source_url = "https://www.indiacode.nic.in/"
    document.document_type = "act"
    document.year = 2023
    document.description = "Digital Personal Data Protection Act 2023"
    document.document_metadata = {
        "source": "India Code",
        "year": 2023,
        "document_type": "act",
    }
    return document


def test_repository_all():
    session = MagicMock()
    document = make_document()

    session.scalars.return_value.all.return_value = [document]

    repository = DocumentRepository(session)

    result = repository.all()

    assert len(result) == 1
    assert result[0]["id"] == "DOC001"
    assert result[0]["title"] == "DPDP Act 2023"
    assert result[0]["year"] == 2023

    session.scalars.assert_called_once()


def test_repository_all_with_search():
    session = MagicMock()
    session.scalars.return_value.all.return_value = []

    repository = DocumentRepository(session)

    result = repository.all(q="DPDP")

    assert result == []
    session.scalars.assert_called_once()


def test_repository_all_with_metadata_filters():
    session = MagicMock()
    document = make_document()

    session.scalars.return_value.all.return_value = [document]

    repository = DocumentRepository(session)

    result = repository.all(
        metadata_filters={
            "source": "India Code",
            "year": 2023,
        }
    )

    assert len(result) == 1
    assert result[0]["metadata"]["source"] == "India Code"


def test_repository_get_found():
    session = MagicMock()
    document = make_document()

    session.scalar.return_value = document

    repository = DocumentRepository(session)

    result = repository.get("DOC001")

    assert result is not None
    assert result["id"] == "DOC001"
    assert result["title"] == "DPDP Act 2023"


def test_repository_get_not_found():
    session = MagicMock()
    session.scalar.return_value = None

    repository = DocumentRepository(session)

    result = repository.get("UNKNOWN")

    assert result is None


def test_repository_to_dict():
    document = make_document()

    result = DocumentRepository._to_dict(document)

    assert result == {
        "id": "DOC001",
        "title": "DPDP Act 2023",
        "source": "India Code",
        "source_url": "https://www.indiacode.nic.in/",
        "document_type": "act",
        "year": 2023,
        "description": "Digital Personal Data Protection Act 2023",
        "metadata": {
            "source": "India Code",
            "year": 2023,
            "document_type": "act",
        },
    }
