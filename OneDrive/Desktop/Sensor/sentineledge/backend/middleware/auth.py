"""
middleware/auth.py — Authentication dependencies for SentinelEdge.

Provides two FastAPI dependency functions:
  - require_admin         — enforces X-Admin-Password header
  - require_subscriber_auth — enforces X-Auth-Token header (subscriber JWT-lite)
"""

from __future__ import annotations

from typing import Any

from fastapi import Header, HTTPException, status

from config import ADMIN_PASSWORD


def require_admin(x_admin_password: str = Header(default=None)) -> bool:
    """
    FastAPI dependency — enforces admin password on protected endpoints.

    Usage:
        @router.post("/subscribers", dependencies=[Depends(require_admin)])

    Raises HTTP 401 if the header is missing or incorrect.
    Returns True on success.
    """
    if not ADMIN_PASSWORD:
        # If no password is configured, admin endpoints are open (dev mode)
        return True
    if x_admin_password != ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Admin-Password header.",
            headers={"WWW-Authenticate": "X-Admin-Password"},
        )
    return True


def require_subscriber_auth(
    x_auth_token: str = Header(default=None),
) -> dict[str, Any]:
    """
    FastAPI dependency — enforces subscriber token on mobile-app endpoints.

    Imports active_tokens lazily to avoid a circular import (auth router
    imports models; models don't import middleware).

    Usage:
        @router.get("/my-alerts", dependencies=[Depends(require_subscriber_auth)])

    Raises HTTP 401 if the token is missing, unknown, or expired.
    Returns the token payload dict on success:
        {"subscriber_id": int, "name": str, "escalation_order": int, "expires_at": datetime}
    """
    from datetime import datetime, timezone
    from routers.auth import active_tokens   # lazy import avoids circular dep

    if not x_auth_token or x_auth_token not in active_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "InvalidToken", "message": "Missing or invalid X-Auth-Token"},
        )
    payload = active_tokens[x_auth_token]
    if datetime.now(timezone.utc) > payload["expires_at"]:
        del active_tokens[x_auth_token]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "TokenExpired", "message": "Token has expired — please log in again"},
        )
    return payload
