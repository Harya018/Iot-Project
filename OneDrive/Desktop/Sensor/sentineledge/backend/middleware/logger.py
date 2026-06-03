"""
middleware/logger.py — Request logging middleware.

Logs method, path, status code, and processing time for every HTTP request.
"""

import logging
import time

from fastapi import Request

logger = logging.getLogger("sentineledge.access")


async def log_requests(request: Request, call_next):
    """Starlette middleware callable: logs each request with timing."""
    start = time.monotonic()
    response = await call_next(request)
    elapsed = (time.monotonic() - start) * 1000
    logger.info(
        "%s %s -> %d (%.1fms)",
        request.method,
        request.url.path,
        response.status_code,
        elapsed,
    )
    return response
