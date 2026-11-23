from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from dpdpcompass.db.models import Document


class DocumentRepository:
    """Read compliance documents from PostgreSQL."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def all(
        self,
        limit: int = 20,
        q: str | None = None,
        metadata_filters: dict[str, Any] | None = None,
        sort: str | None = None,
    ) -> list[dict]:
        """Return documents with optional search, metadata filters, and sorting."""
        statement = select(Document)

        if q:
            search = f"%{q}%"
            statement = statement.where(
                or_(
                    Document.title.ilike(search),
                    Document.description.ilike(search),
                    Document.source.ilike(search),
                    Document.document_type.ilike(search),
                )
            )

        if metadata_filters:
            statement = statement.where(Document.document_metadata.contains(metadata_filters))

        if sort:
            descending = sort.startswith("-")
            column_name = sort[1:] if descending else sort
            column = getattr(Document, column_name)

            statement = statement.order_by(column.desc() if descending else column.asc())
        else:
            statement = statement.order_by(Document.id)

        statement = statement.limit(limit)

        documents = self.session.scalars(statement).all()

        return [self._to_dict(document) for document in documents]

    def stats(self) -> dict:
        """Return total document count and count per source."""
        total = self.session.scalar(select(func.count()).select_from(Document))

        source_counts = self.session.execute(
            select(Document.source, func.count(Document.id))
            .group_by(Document.source)
            .order_by(Document.source)
        ).all()

        return {
            "total": total or 0,
            "by_source": {source: count for source, count in source_counts},
        }

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
            "metadata": document.document_metadata,
        }
