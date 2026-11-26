from pathlib import Path
from uuid import uuid4

import pymupdf

from dpdpcompass.db.models import Document, Page, ParseFailure
from dpdpcompass.ingest.parse import parse_file
from dpdpcompass.ingest.store import store_parse_failure, store_parsed_document


def test_store_parsed_document(db_session, tmp_path: Path) -> None:
    document = Document(
        external_id=f"TEST-PARSE-001-{uuid4().hex[:8]}",
        title="Parser Test",
        source="test",
        source_url="https://example.com/test.pdf",
        document_type="pdf",
        year=2026,
        description="Parser integration test",
        sha256="a" * 64,
        document_metadata={},
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)

    pdf_path = tmp_path / "sample.pdf"
    pdf = pymupdf.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "DPDP Compass parser test")
    pdf.save(pdf_path)
    pdf.close()

    parsed = parse_file(pdf_path)
    parsed.pages[0].headings = ["Test Document"]

    count = store_parsed_document(db_session, parsed, document.id)

    assert count == 1

    stored_page = db_session.query(Page).filter(Page.doc_id == document.id).one()

    assert stored_page.page_no == 1
    assert "DPDP Compass parser test" in stored_page.text
    assert stored_page.headings == ["Test Document"]


def test_store_parse_failure(db_session, tmp_path: Path) -> None:
    path = tmp_path / "broken.pdf"

    store_parse_failure(
        db_session,
        path=path,
        sha256="b" * 64,
        source_url="https://example.com/broken.pdf",
        reason="corrupt",
        detail="Test failure",
    )

    failure = db_session.query(ParseFailure).filter(ParseFailure.path == str(path)).one()

    assert failure.reason == "corrupt"
    assert failure.attempts == 1

    store_parse_failure(
        db_session,
        path=path,
        sha256="c" * 64,
        source_url="https://example.com/broken.pdf",
        reason="corrupt",
        detail="Retry failure",
    )

    db_session.refresh(failure)

    assert failure.attempts == 2
    assert failure.sha256 == "c" * 64
    assert failure.detail == "Retry failure"


def test_store_multiple_parsed_pages(db_session, tmp_path: Path) -> None:
    document = Document(
        external_id=f"TEST-PARSE-002-{uuid4().hex[:8]}",
        title="Multi Page Parser Test",
        source="test",
        source_url="https://example.com/multi-page.pdf",
        document_type="pdf",
        year=2026,
        description="Multi-page parser integration test",
        sha256="d" * 64,
        document_metadata={},
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)

    pdf_path = tmp_path / "multi-page.pdf"
    pdf = pymupdf.open()

    page1 = pdf.new_page()
    page1.insert_text((72, 72), "First page content")

    page2 = pdf.new_page()
    page2.insert_text((72, 72), "Second page content")

    pdf.save(pdf_path)
    pdf.close()

    parsed = parse_file(pdf_path)
    parsed.pages[0].headings = ["Introduction"]
    parsed.pages[1].headings = ["Conclusion"]

    count = store_parsed_document(db_session, parsed, document.id)

    assert count == 2

    pages = db_session.query(Page).filter(Page.doc_id == document.id).order_by(Page.page_no).all()

    assert len(pages) == 2
    assert pages[0].page_no == 1
    assert pages[1].page_no == 2
    assert "First page content" in pages[0].text
    assert "Second page content" in pages[1].text
    assert pages[0].headings == ["Introduction"]
    assert pages[1].headings == ["Conclusion"]
