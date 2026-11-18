from fastapi import APIRouter, Depends, Query, Request

from dpdpcompass.api.deps import get_document_repository
from dpdpcompass.api.errors import not_found_response
from dpdpcompass.db.repository import DocumentRepository

router = APIRouter(prefix="/v1/documents", tags=["documents"])


@router.get("")
def list_documents(
    limit: int = Query(default=20, ge=1, le=100),
    metadata_source: str | None = Query(default=None),
    metadata_year: int | None = Query(default=None),
    metadata_document_type: str | None = Query(default=None),
    repository: DocumentRepository = Depends(get_document_repository),  # noqa: B008
) -> list[dict]:
    """Return documents with optional metadata filters."""
    metadata_filters = {}

    if metadata_source is not None:
        metadata_filters["source"] = metadata_source

    if metadata_year is not None:
        metadata_filters["year"] = metadata_year

    if metadata_document_type is not None:
        metadata_filters["document_type"] = metadata_document_type

    return repository.all(
        limit=limit,
        metadata_filters=metadata_filters or None,
    )


@router.get("/{record_id}")
def get_document(
    record_id: str,
    request: Request,
    repository: DocumentRepository = Depends(get_document_repository),  # noqa: B008
):
    """Return one compliance document by ID."""
    document = repository.get(record_id)

    if document is None:
        return not_found_response(
            request,
            f"Document '{record_id}' was not found.",
        )

    return document
