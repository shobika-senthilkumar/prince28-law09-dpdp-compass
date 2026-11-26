from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dpdpcompass.db.base import Base


class Document(Base):
    """A legal or compliance source document used by DPDP Compass."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)

    # Existing DPDP Compass source information.
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    document_type: Mapped[str] = mapped_column(
        "doc_type",
        String(100),
        nullable=False,
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Day 3 compliance-source metadata.
    licence: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    published_on: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # Fingerprint of the source record for idempotent loading.
    sha256: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    # Flexible metadata used for API filtering.
    document_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
    )

    # Typed copy of metadata["source"] for fast B-tree filtering.
    metadata_source: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    pages: Mapped[list["Page"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index(
            "ix_documents_metadata_gin",
            "metadata",
            postgresql_using="gin",
            postgresql_ops={"metadata": "jsonb_path_ops"},
        ),
    )


class Page(Base):
    """Page-level source text belonging to a compliance document."""

    __tablename__ = "pages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    doc_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    page_no: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    headings: Mapped[list[str]] = mapped_column(
        JSONB,
        server_default="[]",
        nullable=False,
    )

    document: Mapped[Document] = relationship(
        back_populates="pages",
    )

    __table_args__ = (UniqueConstraint("doc_id", "page_no"),)


class ParseFailure(Base):
    """A raw file that could not be parsed."""

    __tablename__ = "parse_failures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    path: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    reason: Mapped[str] = mapped_column(String(40), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    last_attempt_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
