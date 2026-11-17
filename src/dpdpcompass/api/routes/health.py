from fastapi import APIRouter, Depends

from dpdpcompass.api.deps import get_store
from dpdpcompass.store import RecordStore

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    """Basic liveness check."""
    return {"status": "ok"}


@router.get("/ready")
def ready(
    store: RecordStore = Depends(get_store),  # noqa: B008
) -> dict[str, object]:
    """Readiness check based on the loaded record store."""
    return {
        "status": "ready",
        "records": store.count,
    }
