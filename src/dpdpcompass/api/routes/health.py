from fastapi import APIRouter
from sqlalchemy import text

from dpdpcompass.db.session import engine

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    """Basic liveness check."""
    return {"status": "ok"}


@router.get("/ready")
def ready() -> dict[str, object]:
    """Readiness check based on the PostgreSQL database."""
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
        records = connection.execute(text("SELECT COUNT(*) FROM documents")).scalar_one()

    return {
        "status": "ready",
        "records": records,
    }
