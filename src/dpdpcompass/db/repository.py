from sqlalchemy import select
from sqlalchemy.orm import Session

from dpdpcompass.db.models import Document


class DocumentRepository:
    """Read compliance documents from PostgreSQL."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def all(self, limit: int = 20) -> list[dict]:
        """Return documents ordered by their database ID."""
        statement = select(Document).order_by(Document.id).limit(limit)
        documents = self.session.scalars(statement).all()

        return [self._to_dict(document) for document in documents]

    def get(self, external_id: str) -> dict | None:
        """Return one document by its external ID."""
        statement = select(Document).where(Document.external_id == external_id)
        document = self.session.scalar(statement)

        if document is None:
            return None

        return self._to_dict(document)

    @staticmethod
    def _to_dict(document: Document) -> dict:
        """Convert a database document to the API response shape."""
        return {
            "id": document.external_id,
            "title": document.title,
            "source": document.source,
            "source_url": document.source_url,
            "document_type": document.document_type,
            "year": document.year,
            "description": document.description,
        }
