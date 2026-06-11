"""
middleware/rate_limit.py — Shared slowapi Limiter instance.

Import `limiter` into each router and decorate endpoints with
@limiter.limit("N/minute").

The Limiter is registered on `app.state.limiter` in main.py, and
the RateLimitExceeded exception handler is also wired up there.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Key function: rate-limit per remote IP address.
limiter = Limiter(key_func=get_remote_address)
