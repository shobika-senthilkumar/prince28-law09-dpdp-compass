from collections.abc import Generator

from dpdpcompass.db.repository import DocumentRepository
from dpdpcompass.db.session import SessionLocal


def get_document_repository() -> Generator[DocumentRepository, None, None]:
    """Provide a PostgreSQL document repository for a request."""
    with SessionLocal() as session:
        yield DocumentRepository(session)
