import pytest


class FakeRepo:
    def __init__(self):
        self.documents = [
            {
                "id": "1",
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
        ]

    def all(self, limit=20, q=None, metadata_filters=None):
        documents = self.documents[:limit]

        if q:
            search = q.lower()
            documents = [
                document
                for document in documents
                if search in document["title"].lower()
                or search in document["description"].lower()
                or search in document["source"].lower()
                or search in document["document_type"].lower()
            ]

        if metadata_filters:
            documents = [
                document
                for document in documents
                if all(
                    document["metadata"].get(key) == value
                    for key, value in metadata_filters.items()
                )
            ]

        return documents


@pytest.fixture
def fake_repo():
    return FakeRepo()
