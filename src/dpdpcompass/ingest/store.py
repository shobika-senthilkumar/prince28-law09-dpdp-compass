from pathlib import Path

from sqlalchemy.orm import Session

from dpdpcompass.db.models import Page
from dpdpcompass.ingest.parse import ParsedDoc


def store_parsed_document(
    session: Session,
    parsed: ParsedDoc,
    document_id: int,
) -> int:
    """Store parsed pages for an existing document."""
    session.query(Page).filter(Page.doc_id == document_id).delete(synchronize_session=False)

    for parsed_page in parsed.pages:
        session.add(
            Page(
                doc_id=document_id,
                page_no=parsed_page.page_no,
                text=parsed_page.text,
                headings=parsed_page.headings,
            )
        )

    session.commit()

    return len(parsed.pages)


def store_parse_failure(
    session: Session,
    path: Path,
    sha256: str,
    source_url: str | None,
    reason: str,
    detail: str | None = None,
) -> None:
    """Create or update a parse failure record."""
    from dpdpcompass.db.models import ParseFailure

    failure = session.query(ParseFailure).filter(ParseFailure.path == str(path)).first()

    if failure is None:
        failure = ParseFailure(
            path=str(path),
            sha256=sha256,
            source_url=source_url,
            reason=reason,
            detail=detail,
            attempts=1,
        )
        session.add(failure)
    else:
        failure.sha256 = sha256
        failure.source_url = source_url
        failure.reason = reason
        failure.detail = detail
        failure.attempts += 1

    session.commit()
