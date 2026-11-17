from fastapi import Request

from dpdpcompass.store import RecordStore


def get_store(request: Request) -> RecordStore:
    """Return the application record store."""
    return request.app.state.store
