"""
middleware/rate_limiter.py — In-memory rate limiter for SentinelEdge.

No external dependencies. Uses a sliding window algorithm per client IP.
Only applied to abuse-prone endpoints — limits are generous for legitimate use.

Usage (in router):
    from middleware.rate_limiter import rate_limiter
    from fastapi import Request
    from fastapi.responses import JSONResponse

    def check_rate(request: Request, limit: int = 5, window: int = 60):
        if not rate_limiter.is_allowed(request.client.host, limit, window):
            return JSONResponse(
                status_code=429,
                content={...},
                headers={"Retry-After": str(window)},
            )
        return None
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta

from utils.logger import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """
    Simple in-memory sliding-window rate limiter.

    State is lost on server restart — intentional for simplicity.
    For persistent rate limiting, use Redis.
    """

    def __init__(self) -> None:
        # Maps client_ip → list[datetime] of recent request timestamps
        self._requests: dict[str, list[datetime]] = defaultdict(list)

    def is_allowed(
        self,
        client_ip: str,
        limit: int,
        window_seconds: int,
    ) -> bool:
        """
        Return True if this client is within the allowed rate.

        Side-effect: records this request if allowed.

        Args:
            client_ip:      The requesting client's IP address.
            limit:          Maximum requests allowed in the window.
            window_seconds: Duration of the sliding window in seconds.
        """
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_seconds)

        # Evict timestamps outside the window
        self._requests[client_ip] = [
            t for t in self._requests[client_ip] if t > window_start
        ]

        if len(self._requests[client_ip]) >= limit:
            logger.warning(
                "Rate limit hit: %s made %d requests in %ds (limit: %d)",
                client_ip, len(self._requests[client_ip]), window_seconds, limit,
            )
            return False

        self._requests[client_ip].append(now)
        return True

    def remaining(self, client_ip: str, limit: int, window_seconds: int) -> int:
        """Return how many requests this client has left in the current window."""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_seconds)
        recent = [t for t in self._requests[client_ip] if t > window_start]
        return max(0, limit - len(recent))

    def reset(self, client_ip: str) -> None:
        """Clear rate-limit state for a client (useful in tests)."""
        self._requests.pop(client_ip, None)


# Module-level singleton shared by all routers
rate_limiter = RateLimiter()


# ── FastAPI dependency helpers ────────────────────────────────────────────────

def make_rate_limit_response(window_seconds: int = 60) -> dict:
    """Build the standard 429 response body."""
    return {
        "error": "RateLimitError",
        "message": f"Too many requests. Try again in {window_seconds}s.",
        "retry_after": window_seconds,
    }
