from __future__ import annotations

import argparse
from pathlib import Path

from dpdpcompass.db.models import Document
from dpdpcompass.db.session import SessionLocal
from dpdpcompass.ingest.fetch import Manifest
from dpdpcompass.ingest.parse import ParseError, parse_file
from dpdpcompass.ingest.store import store_parse_failure, store_parsed_document


def load_manifest_records(root: Path) -> list[dict]:
    manifest = Manifest(root / "data" / "manifest.jsonl")
    records = []

    for record in manifest.records.values():
        if record.get("status") != "downloaded":
            continue

        raw_path = root / record["path"]
        if raw_path.is_file():
            records.append(record)

    return records


def find_document(session, record: dict) -> Document | None:
    sha256 = record.get("sha256")
    source_url = record.get("url")
    title = record.get("title")

    if sha256:
        document = session.query(Document).filter(Document.sha256 == sha256).first()
        if document:
            return document

    if source_url:
        document = session.query(Document).filter(Document.source_url == source_url).first()
        if document:
            return document

    if title:
        return session.query(Document).filter(Document.title == title).first()

    return None


def parse_one(root: Path, record: dict, session) -> tuple[str, str]:
    path = root / record["path"]

    try:
        parsed = parse_file(path)

        document = find_document(session, record)

        if document is None:
            sha256 = record.get("sha256", "")
            external_id = f"manifest-{sha256[:12]}"

            document = Document(
                external_id=external_id,
                title=record.get("title") or path.stem,
                source=record.get("source", "unknown"),
                source_url=record.get("url", ""),
                document_type=record.get("document_type", "Unknown"),
                year=record.get("year", 2025),
                description=record.get("title") or path.stem,
                licence=record.get("licence"),
                sha256=sha256,
                document_metadata={
                    "manifest_path": record.get("path"),
                    "content_type": record.get("content_type"),
                    "parser": parsed.metadata["parser"],
                    "pages": len(parsed.pages),
                },
                metadata_source="data/manifest.jsonl",
            )

            session.add(document)
            session.flush()

        store_parsed_document(
            session,
            parsed,
            document.id,
        )

        metadata = dict(document.document_metadata or {})
        metadata["parser"] = parsed.metadata["parser"]
        metadata["pages"] = len(parsed.pages)
        document.document_metadata = metadata
        session.commit()

        return "parsed", path.as_posix()

    except ParseError as exc:
        store_parse_failure(
            session,
            path=path,
            sha256=record.get("sha256", ""),
            source_url=record.get("url"),
            reason=exc.args[0] if exc.args else "parse_error",
            detail=str(exc.args[1]) if len(exc.args) > 1 else str(exc),
        )
        reason = exc.args[0] if exc.args else "parse_error"
        return "failed", f"{path.as_posix()} [{reason}]"

    except Exception as exc:
        session.rollback()

        store_parse_failure(
            session,
            path=path,
            sha256=record.get("sha256", ""),
            source_url=record.get("url"),
            reason="error",
            detail=f"{type(exc).__name__}: {exc}",
        )
        return "failed", f"{path.as_posix()} [error: {exc}]"


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse downloaded DPDP Compass corpus files.")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--retry-failed", action="store_true")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    records = load_manifest_records(root)

    if args.retry_failed:
        with SessionLocal() as session:
            from dpdpcompass.db.models import ParseFailure

            failed_paths = {
                str(root / failure.path).replace("\\", "/")
                for failure in session.query(ParseFailure).all()
            }

        records = [
            record
            for record in records
            if str(root / record["path"]).replace("\\", "/") in failed_paths
        ]

    if args.limit:
        records = records[: args.limit]

    parsed = 0
    failed = 0

    with SessionLocal() as session:
        for index, record in enumerate(records, start=1):
            status, detail = parse_one(root, record, session)

            if status == "parsed":
                parsed += 1
            else:
                failed += 1

            print(f"[{index}/{len(records)}] {status}: {detail}")

    print()
    print("Parse summary")
    print(f"  files considered: {len(records)}")
    print(f"  parsed: {parsed}")
    print(f"  failed: {failed}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
