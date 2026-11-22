"""add typed metadata source

Revision ID: 98feccf322b2
Revises: 9a07f4ac15f6
Create Date: 2026-11-22 20:29:41.988276

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "98feccf322b2"  # pragma: allowlist secret
down_revision: str | Sequence[str] | None = "9a07f4ac15f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add typed metadata_source column and backfill it from JSONB metadata."""
    op.add_column(
        "documents",
        sa.Column(
            "metadata_source",
            sa.String(length=255),
            nullable=True,
        ),
    )

    op.execute(
        sa.text(
            """
            UPDATE documents
            SET metadata_source = metadata ->> 'source'
            WHERE metadata ->> 'source' IS NOT NULL
            """
        )
    )

    op.create_index(
        "ix_documents_metadata_source",
        "documents",
        ["metadata_source"],
        unique=False,
    )


def downgrade() -> None:
    """Remove the typed metadata_source column and its index."""
    op.drop_index(
        "ix_documents_metadata_source",
        table_name="documents",
    )
    op.drop_column("documents", "metadata_source")
