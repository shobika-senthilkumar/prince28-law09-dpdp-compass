from fastapi import APIRouter, Depends, Query, Request

from dpdpcompass.api.deps import get_store
from dpdpcompass.api.errors import not_found_response
from dpdpcompass.store import RecordStore

router = APIRouter(prefix="/v1/documents", tags=["documents"])


@router.get("")
def list_documents(
    limit: int = Query(default=20, ge=1, le=100),
    store: RecordStore = Depends(get_store),  # noqa: B008
) -> list[dict]:
    """Return a limited list of compliance records."""
    return store.all()[:limit]


@router.get("/{record_id}")
def get_document(
    record_id: str,
    request: Request,
    store: RecordStore = Depends(get_store),  # noqa: B008
):
    """Return one compliance record by ID."""
    record = store.get(record_id)

    if record is None:
        return not_found_response(
            request,
            f"Document '{record_id}' was not found.",
        )

    return record
