"""
utils/security.py — Credential hashing utilities for SentinelEdge.

Uses bcrypt for all PIN / password storage.  bcrypt automatically:
  - Generates a unique salt per call (no separate salt management).
  - Embeds the cost factor in the hash string ($2b$12$...).
  - Is slow enough to resist offline brute-force attacks.

Public API
----------
hash_pin(plain_pin)          → bcrypt hash string (stored in DB)
verify_pin(plain_pin, hash)  → True if plain matches the stored hash
"""

from __future__ import annotations

import bcrypt

from utils.logger import get_logger

logger = get_logger(__name__)


def hash_pin(plain_pin: str) -> str:
    """Hash a PIN (or password) using bcrypt.

    Returns the hashed string suitable for storage in the database.
    The returned value always starts with '$2b$' (bcrypt identifier).
    """
    hashed = bcrypt.hashpw(plain_pin.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_pin(plain_pin: str, hashed_pin: str) -> bool:
    """Verify a plain-text PIN against a stored bcrypt hash.

    Returns True if *plain_pin* matches *hashed_pin*, False otherwise.
    Never raises — returns False on any error (e.g. malformed hash).
    """
    try:
        return bcrypt.checkpw(plain_pin.encode("utf-8"), hashed_pin.encode("utf-8"))
    except Exception as exc:
        logger.warning("verify_pin: comparison error: %s", exc)
        return False
