from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from dpdpcompass.db.session import engine

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    """Basic liveness check."""
    return {"status": "ok"}


@router.get("/ready")
def ready() -> JSONResponse:
    """Readiness check based on the PostgreSQL database."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return JSONResponse(
            status_code=200,
            content={
                "status": "ready",
                "checks": {
                    "database": True,
                },
            },
        )

    except SQLAlchemyError:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "checks": {
                    "database": False,
                },
            },
        )
