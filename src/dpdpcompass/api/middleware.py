import time
import uuid

from fastapi import Request
from fastapi.responses import JSONResponse


async def request_middleware(request: Request, call_next):
    """Add request ID, timing, and a crash-safe error response."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    start = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

        return JSONResponse(
            status_code=500,
            content={
                "type": "about:blank",
                "title": "Internal Server Error",
                "status": 500,
                "detail": "An unexpected error occurred.",
            },
            media_type="application/problem+json",
            headers={
                "X-Request-ID": request_id,
            },
        )

    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-Ms"] = str(elapsed_ms)

    return response
