from pathlib import Path
from unittest.mock import MagicMock

from dpdpcompass.db.loader import (
    build_metadata,
    calculate_sha256,
    load_documents,
)


def sample_record():
    return {
        "id": "DOC001",
        "title": "DPDP Act 2023",
        "source": "India Code",
        "source_url": "https://www.indiacode.nic.in/",
        "document_type": "act",
        "year": 2023,
        "description": "Digital Personal Data Protection Act 2023",
    }


def test_calculate_sha256_is_stable():
    record = sample_record()

    first_hash = calculate_sha256(record)
    second_hash = calculate_sha256(record)

    assert first_hash == second_hash
    assert len(first_hash) == 64


def test_build_metadata():
    record = sample_record()

    metadata = build_metadata(record)

    assert metadata == {
        "source": "India Code",
        "year": 2023,
        "document_type": "act",
    }


def test_load_documents_inserts_new_document(tmp_path: Path):
    data_file = tmp_path / "documents.json"
    data_file.write_text(
        '[{"id":"DOC001","title":"DPDP Act 2023","source":"India Code",'
        '"source_url":"https://www.indiacode.nic.in/","document_type":"act",'
        '"year":2023,"description":"Digital Personal Data Protection Act 2023"}]',
        encoding="utf-8",
    )

    session = MagicMock()
    session.scalar.return_value = None

    changed = load_documents(session, data_file)

    assert changed == 1
    session.add.assert_called_once()
    session.commit.assert_called_once()


def test_load_documents_updates_changed_document(tmp_path: Path):
    data_file = tmp_path / "documents.json"
    data_file.write_text(
        '[{"id":"DOC001","title":"Updated DPDP Act 2023","source":"India Code",'
        '"source_url":"https://www.indiacode.nic.in/","document_type":"act",'
        '"year":2023,"description":"Updated description"}]',
        encoding="utf-8",
    )

    existing = MagicMock()
    existing.sha256 = "old-hash"
    existing.document_metadata = {"source": "Old Source"}

    session = MagicMock()
    session.scalar.return_value = existing

    changed = load_documents(session, data_file)

    assert changed == 1
    assert existing.title == "Updated DPDP Act 2023"
    assert existing.description == "Updated description"
    assert existing.sha256 != "old-hash"
    session.add.assert_not_called()
    session.commit.assert_called_once()
