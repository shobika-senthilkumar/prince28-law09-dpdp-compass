"""add pages and compliance metadata

Revision ID: 9a07f4ac15f6
Revises: d35011953d70
Create Date: 2026-11-18 15:07:44.257631

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9a07f4ac15f6"  # pragma: allowlist secret
down_revision: str | Sequence[str] | None = "d35011953d70"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Rename the existing DPDP-specific document_type field to the
    # standardized doc_type field used by the Day 3 data model.
    op.alter_column(
        "documents",
        "document_type",
        new_column_name="doc_type",
    )

    # Add compliance-source metadata fields.
    op.add_column(
        "documents",
        sa.Column("licence", sa.String(length=200), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column("published_on", sa.Date(), nullable=True),
    )

    # Create the page-level source content table.
    op.create_table(
        "pages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("doc_id", sa.Integer(), nullable=False),
        sa.Column("page_no", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["doc_id"],
            ["documents.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("doc_id", "page_no"),
    )

    op.create_index(
        "ix_pages_doc_id",
        "pages",
        ["doc_id"],
        unique=False,
    )

    # GIN makes JSONB containment filters efficient.
    op.create_index(
        "ix_documents_metadata_gin",
        "documents",
        ["metadata"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"metadata": "jsonb_path_ops"},
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        "ix_documents_metadata_gin",
        table_name="documents",
    )

    op.drop_index(
        "ix_pages_doc_id",
        table_name="pages",
    )

    op.drop_table("pages")

    op.drop_column("documents", "published_on")
    op.drop_column("documents", "licence")

    op.alter_column(
        "documents",
        "doc_type",
        new_column_name="document_type",
    )
