from fastapi import Request
from fastapi.responses import JSONResponse

from core.settings import settings


async def limit_request_size(request: Request, call_next):
    """Reject oversized uploads by Content-Length, before Starlette spools the
    multipart body to disk. Per-file limits are checked later, per file."""
    size = request.headers.get("content-length")
    if size and size.isdigit() and int(size) > settings.api.max_request_bytes:
        return JSONResponse({"detail": "Request body too large"}, status_code=413)
    return await call_next(request)
