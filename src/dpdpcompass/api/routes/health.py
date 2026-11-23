"""Health and readiness endpoints."""

from fastapi import APIRouter, Response, status
from sqlalchemy import func, select, text

from dpdpcompass.config import get_settings
from dpdpcompass.db.models import Document
from dpdpcompass.db.session import SessionLocal

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    """Return application health and deployed version."""
    settings = get_settings()

    return {
        "status": "ok",
        "app": settings.app_name,
        "env": settings.app_env,
        "version": settings.git_sha,
    }


@router.get("/ready")
def ready(response: Response) -> dict:
    """Check whether the application can reach the database and has enough records."""
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))

            records_count = session.scalar(select(func.count()).select_from(Document)) or 0

        if records_count < 20:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            return {
                "status": "not_ready",
                "checks": {"database": True},
                "records_count": records_count,
            }

        return {
            "status": "ready",
            "checks": {"database": True},
            "records_count": records_count,
        }

    except Exception:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "not_ready",
            "checks": {"database": False},
            "records_count": 0,
        }
