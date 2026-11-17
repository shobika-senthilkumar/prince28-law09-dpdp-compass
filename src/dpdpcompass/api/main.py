from contextlib import asynccontextmanager

from fastapi import FastAPI

from dpdpcompass.api.middleware import request_middleware
from dpdpcompass.api.routes.documents import router as documents_router
from dpdpcompass.api.routes.health import router as health_router
from dpdpcompass.config import get_settings
from dpdpcompass.logging_setup import setup_logging
from dpdpcompass.store import RecordStore


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load application resources when the API starts."""
    settings = get_settings()
    setup_logging(settings.log_level)

    store = RecordStore(settings.data_file)
    store.load()
    app.state.store = store

    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="DPDP Compass",
        description="AI-powered compliance guidance for India's DPDP framework.",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.middleware("http")(request_middleware)

    app.include_router(health_router)
    app.include_router(documents_router)

    return app
