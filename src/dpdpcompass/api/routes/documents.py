from fastapi import APIRouter, Depends, HTTPException, Query, Request

from dpdpcompass.api.deps import get_document_repository
from dpdpcompass.api.errors import not_found_response
from dpdpcompass.db.repository import DocumentRepository

router = APIRouter(prefix="/v1/documents", tags=["documents"])

RESERVED_QUERY_PARAMS = {
    "q",
    "limit",
    "metadata_source",
    "metadata_year",
    "metadata_document_type",
}


@router.get("")
def list_documents(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    q: str | None = Query(default=None),
    metadata_source: str | None = Query(default=None),
    metadata_year: int | None = Query(default=None),
    metadata_document_type: str | None = Query(default=None),
    repository: DocumentRepository = Depends(get_document_repository),  # noqa: B008
) -> list[dict]:
    """Return documents with search and metadata filters."""
    metadata_filters = {}

    if metadata_source is not None:
        metadata_filters["source"] = metadata_source

    if metadata_year is not None:
        metadata_filters["year"] = metadata_year

    if metadata_document_type is not None:
        metadata_filters["document_type"] = metadata_document_type

    for key, value in request.query_params.multi_items():
        if key in RESERVED_QUERY_PARAMS:
            continue

        if key not in {"source", "year", "document_type"}:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid metadata filter: '{key}'",
            )

        if key == "year":
            try:
                value = int(value)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Metadata filter 'year' must be an integer.",
                ) from None

        metadata_filters[key] = value

    return repository.all(
        limit=limit,
        q=q,
        metadata_filters=metadata_filters or None,
    )


@router.get("/{record_id}")
def get_document(
    record_id: str,
    request: Request,
    repository: DocumentRepository = Depends(get_document_repository),  # noqa: B008
):
    """Return one document by ID."""
    document = repository.get(record_id)

    if document is None:
        return not_found_response(
            request,
            f"Document '{record_id}' was not found.",
        )

    return document
