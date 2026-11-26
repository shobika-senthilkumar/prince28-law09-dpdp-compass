from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from dpdpcompass.api.deps import get_document_repository
from dpdpcompass.api.errors import not_found_response
from dpdpcompass.db.repository import DocumentRepository

router = APIRouter(prefix="/v1/documents", tags=["documents"])


class Record(BaseModel):
    """API response model for a document record."""

    id: str
    title: str
    source: str
    source_url: str | None
    document_type: str
    year: int | None
    description: str | None
    metadata: dict


RESERVED_QUERY_PARAMS = {
    "q",
    "limit",
    "sort",
    "metadata_source",
    "metadata_year",
    "metadata_document_type",
}

ALLOWED_SORT_COLUMNS = {
    "title",
    "published_on",
}


@router.get("", response_model=list[Record])
def list_documents(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    q: str | None = Query(default=None),
    sort: str | None = Query(default=None),
    metadata_source: str | None = Query(default=None),
    metadata_year: int | None = Query(default=None),
    metadata_document_type: str | None = Query(default=None),
    repository: DocumentRepository = Depends(get_document_repository),  # noqa: B008
) -> list[Record]:
    """Return documents with search, metadata filters, and sorting."""
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

    if sort is not None:
        sort_column = sort.lstrip("-")

        if sort_column not in ALLOWED_SORT_COLUMNS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid sort column: '{sort_column}'",
            )

    return repository.all(
        limit=limit,
        q=q,
        metadata_filters=metadata_filters or None,
        sort=sort,
    )


@router.get("/stats")
def document_stats(
    repository: DocumentRepository = Depends(get_document_repository),  # noqa: B008
) -> dict:
    """Return document count and count per source."""
    return repository.stats()


@router.get("/{record_id}/pages")
def get_document_page(
    record_id: str,
    request: Request,
    page_no: int = Query(..., ge=1),
    repository: DocumentRepository = Depends(get_document_repository),  # noqa: B008
) -> dict:
    """Return one page from a document."""
    page = repository.get_page(record_id, page_no)

    if page is None:
        return not_found_response(
            request,
            f"Page '{page_no}' for document '{record_id}' was not found.",
        )

    return page


@router.get("/{record_id}", response_model=Record)
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
