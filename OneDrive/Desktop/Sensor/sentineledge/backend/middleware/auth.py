"""
middleware/auth.py — Admin authentication dependency (Addition 10).

Admin-protected endpoints require the X-Admin-Password header matching
the ADMIN_PASSWORD env variable.
"""

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
