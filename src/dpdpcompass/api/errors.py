from fastapi import Request
from fastapi.responses import JSONResponse


def not_found_response(request: Request, detail: str) -> JSONResponse:
    """Return an RFC 9457-style problem detail response."""
    return JSONResponse(
        status_code=404,
        content={
            "type": "about:blank",
            "title": "Not Found",
            "status": 404,
            "detail": detail,
        },
        media_type="application/problem+json",
        headers={"X-Request-ID": request.state.request_id},
    )
