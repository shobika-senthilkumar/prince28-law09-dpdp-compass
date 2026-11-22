import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from sqlalchemy import delete, select

from dpdpcompass.config import Settings
from dpdpcompass.db.models import Document
from dpdpcompass.db.session import SessionLocal


def calculate_sha256(record: dict[str, Any]) -> str:
    payload = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")

    return hashlib.sha256(payload).hexdigest()


def build_metadata(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": record.get("source"),
        "year": record.get("year"),
        "document_type": record.get("document_type"),
    }


def load_documents(data_file: Path, prune: bool = False) -> None:
    with data_file.open("r", encoding="utf-8") as file:
        records: list[dict[str, Any]] = json.load(file)

    inserted = 0
    updated = 0
    unchanged = 0
    deleted = 0

    current_ids = {str(record["id"]) for record in records}

    with SessionLocal() as session:
        for record in records:
            external_id = str(record["id"])
            record_hash = calculate_sha256(record)
            metadata = build_metadata(record)

            existing = session.scalar(select(Document).where(Document.external_id == external_id))

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
                inserted += 1

            elif existing.sha256 != record_hash:
                existing.title = record["title"]
                existing.source = record["source"]
                existing.source_url = record["source_url"]
                existing.document_type = record["document_type"]
                existing.year = record["year"]
                existing.description = record["description"]
                existing.document_metadata = metadata
                existing.sha256 = record_hash
                updated += 1

            else:
                unchanged += 1

        if prune:
            existing_ids = set(session.scalars(select(Document.external_id)).all())
            stale_ids = existing_ids - current_ids

            if stale_ids:
                result = session.execute(
                    delete(Document).where(Document.external_id.in_(stale_ids))
                )
                deleted = result.rowcount or 0

        session.commit()

    print(
        f"records={len(records)} "
        f"inserted={inserted} "
        f"updated={updated} "
        f"unchanged={unchanged} "
        f"deleted={deleted}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--prune",
        action="store_true",
        help="Delete database documents missing from the JSON file.",
    )
    args = parser.parse_args()

    load_dotenv()

    data_file = Path(Settings().data_file)
    load_documents(data_file, prune=args.prune)
