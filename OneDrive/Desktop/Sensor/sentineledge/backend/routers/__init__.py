"""backend/routers — FastAPI APIRouter modules, one per resource domain."""

from routers.alerts import router as alerts_router
from routers.subscribers import router as subscribers_router
from routers.config import router as config_router
from routers.simulate import router as simulate_router
from routers.health import router as health_router
from routers.admin import router as admin_router

__all__ = [
    "alerts_router",
    "subscribers_router",
    "config_router",
    "simulate_router",
    "health_router",
    "admin_router",
]
