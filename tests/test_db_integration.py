import os

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from dpdpcompass.db.models import Document

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="TEST_DATABASE_URL is not configured",
)


@pytest.fixture
def db_session():
    engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)

    with Session(engine) as session:
        yield session

    engine.dispose()


def test_database_connection(db_session):
    result = db_session.execute(text("SELECT 1")).scalar_one()

    assert result == 1


def test_documents_table_has_data(db_session):
    document = db_session.execute(select(Document).limit(1)).scalar_one_or_none()

    assert document is not None
    assert document.external_id
    assert document.title


def test_document_round_trip(db_session):
    document = Document(
        external_id="integration-test-001",
        title="Integration Test Document",
        source="Integration Test",
        source_url="https://example.com/integration-test",
        document_type="test",
        year=2026,
        description="Temporary document used by the integration test.",
        licence="Test",
        sha256="0" * 64,
        document_metadata={"source": "Integration Test"},
        metadata_source="Integration Test",
    )

    db_session.add(document)
    db_session.flush()

    saved = db_session.execute(
        select(Document).where(Document.external_id == "integration-test-001")
    ).scalar_one()

    assert saved.title == "Integration Test Document"
    assert saved.metadata_source == "Integration Test"

    db_session.rollback()
