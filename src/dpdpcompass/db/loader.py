import hashlib
import json
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from dpdpcompass.db.models import Document


def calculate_sha256(record: dict[str, Any]) -> str:
    """Return a stable SHA-256 hash for a record."""
    payload = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")

    return hashlib.sha256(payload).hexdigest()


def build_metadata(record: dict[str, Any]) -> dict[str, Any]:
    """Build filterable JSONB metadata from a source record."""
    return {
        "source": record.get("source"),
        "year": record.get("year"),
        "document_type": record.get("document_type"),
    }


def load_documents(
    session: Session,
    data_file: Path,
) -> int:
    """Insert new documents and update changed documents.

    Returns the number of records inserted or updated.
    """
    with data_file.open("r", encoding="utf-8") as file:
        records: list[dict[str, Any]] = json.load(file)

    changed_count = 0

    for record in records:
        external_id = str(record["id"])
        record_hash = calculate_sha256(record)

        existing = session.scalar(
            select(Document).where(
                Document.external_id == external_id,
            )
        )

        metadata = build_metadata(record)

        if existing is None:
            session.add(
                Document(
                    external_id=external_id,
                    title=record["title"],
                    source=record["source"],
                    source_url=record["source_url"],
                    document_type=record["document_type"],
                    year=record["year"],
                    description=record["description"],
                    document_metadata=metadata,
                    sha256=record_hash,
                )
            )
            changed_count += 1
            continue

        if existing.sha256 != record_hash or existing.document_metadata != metadata:
            existing.title = record["title"]
            existing.source = record["source"]
            existing.source_url = record["source_url"]
            existing.document_type = record["document_type"]
            existing.year = record["year"]
            existing.description = record["description"]
            existing.document_metadata = metadata
            existing.sha256 = record_hash
            changed_count += 1

    session.commit()
    return changed_count


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    from dpdpcompass.config import Settings
    from dpdpcompass.db.session import SessionLocal

    with SessionLocal() as session:
        changed = load_documents(
            session=session,
            data_file=Path(Settings().data_file),
        )

    print(f"Loaded {changed} new or changed documents.")
