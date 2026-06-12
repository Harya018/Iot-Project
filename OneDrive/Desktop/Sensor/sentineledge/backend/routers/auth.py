"""
routers/auth.py — Mobile app authentication endpoints.

Provides name + PIN login for subscribers.
Tokens are stored in-memory; cleared on server restart.
Clients (React Native) store the token in AsyncStorage and re-login on restart.

Endpoints
---------
POST /api/auth/login    — public; returns a 64-char hex token (30-day TTL)
                          Rate limited: 10/minute per IP (brute-force protection)
POST /api/auth/logout   — requires X-Auth-Token header
GET  /api/auth/me       — requires X-Auth-Token header
POST /api/auth/admin-login  — sub-admin/admin dashboard login (uses DB sessions)
GET  /api/auth/admin-me     — returns current admin session info
"""



import secrets
from datetime import datetime, timezone, timedelta
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator

import database
from models import LoginIn, LoginOut
from middleware.rate_limit import limiter
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Auth"])

# ── In-memory subscriber token store ─────────────────────────────────────────
# Key: token (64-char hex string)
# Value: {"subscriber_id": int, "name": str, "escalation_order": int,
#         "expires_at": datetime}
#
# Cleared on every server restart — clients must re-login.
active_tokens: dict[str, dict[str, Any]] = {}

_TOKEN_TTL_DAYS = 30


def _get_valid_token(x_auth_token: str | None) -> dict[str, Any]:
    """Validate a token header and return its payload, or raise HTTP 401."""
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


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/login",
    response_model=LoginOut,
    summary="Subscriber login",
    description="Authenticate with name + PIN. Returns a 30-day bearer token. Rate limited: 10/min.",
)
@limiter.limit("10/minute")
async def login(body: LoginIn, request: Request) -> LoginOut:
    subscriber = database.get_subscriber_by_name_and_pin(body.name, body.pin)
    if subscriber is None:
        logger.warning("Failed login attempt for name=%r", body.name)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "InvalidCredentials", "message": "Name or PIN is incorrect"},
        )

    token = secrets.token_hex(32)          # 64-char hex string
    expires_at = datetime.now(timezone.utc) + timedelta(days=_TOKEN_TTL_DAYS)
    active_tokens[token] = {
        "subscriber_id":    subscriber["id"],
        "name":             subscriber["name"],
        "escalation_order": subscriber["escalation_order"],
        "expires_at":       expires_at,
    }
    logger.info("Login successful for subscriber id=%d name=%r", subscriber["id"], subscriber["name"])
    return LoginOut(
        token=token,
        subscriber_id=subscriber["id"],
        name=subscriber["name"],
        escalation_order=subscriber["escalation_order"],
    )


@router.post(
    "/logout",
    summary="Subscriber logout",
    description="Invalidates the supplied token. Requires X-Auth-Token header.",
)
async def logout(x_auth_token: str = Header(default=None)):
    _get_valid_token(x_auth_token)   # raises 401 if bad
    del active_tokens[x_auth_token]
    logger.info("Token invalidated (logout)")
    return {"message": "Logged out"}


@router.get(
    "/me",
    summary="Current subscriber",
    description="Returns the subscriber details for the current token.",
)
async def me(x_auth_token: str = Header(default=None)):
    payload = _get_valid_token(x_auth_token)
    return {
        "subscriber_id":    payload["subscriber_id"],
        "name":             payload["name"],
        "escalation_order": payload["escalation_order"],
        "expires_at":       payload["expires_at"].isoformat(),
    }


# ── Sub-admin session login (DB-backed) ───────────────────────────────────────
# Sub-admins log in with name+password (stored in the admins table).
# Sessions are stored in admin_sessions PostgreSQL table and survive restarts.
# Session TTL: 8 hours.

class _AdminLoginIn(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=200)

    @field_validator("name", "password", mode="before")
    @classmethod
    def strip_fields(cls, v: str) -> str:
        return v.strip() if isinstance(v, str) else v


@router.post(
    "/admin-login",
    summary="Sub-admin / Admin dashboard login",
    description=(
        "Authenticate a dashboard user (main admin or sub-admin) with "
        "name + password. Returns role so the client can route to the "
        "correct dashboard. Session TTL: 8 hours. Session persists across restarts. "
        "Rate limited: 10/minute per IP."
    ),
)
@limiter.limit("10/minute")
async def admin_login(body: _AdminLoginIn, request: Request):
    """Login for the admin dashboard (main or sub-admin)."""
    admin = database.verify_admin_password(body.name, body.password)
    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "InvalidCredentials", "message": "Name or password is incorrect"},
        )
    token = secrets.token_hex(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=8)

    # Persist session in PostgreSQL
    database.create_session(token, expires_at)

    logger.info("Admin login: name=%r role=%s", admin["name"], admin["role"])
    return {
        "token":    token,
        "admin_id": admin["id"],
        "name":     admin["name"],
        "role":     admin["role"],
        "message":  "Login successful",
    }


@router.get(
    "/admin-me",
    summary="Current admin session info",
    description="Returns session info for the given admin token (X-Admin-Token header).",
)
async def admin_me(x_admin_token: str = Header(default=None)):
    """Return the current sub-admin session info."""
    if not x_admin_token:
        raise HTTPException(status_code=401, detail="Missing X-Admin-Token")

    session = database.get_session(x_admin_token)
    if session is None:
        raise HTTPException(status_code=401, detail="Invalid or expired X-Admin-Token")

    return {
        "token":       x_admin_token,
        "created_at":  session["created_at"].isoformat() if session.get("created_at") else None,
        "expires_at":  session["expires_at"].isoformat() if session.get("expires_at") else None,
        "last_used_at": session["last_used_at"].isoformat() if session.get("last_used_at") else None,
    }
