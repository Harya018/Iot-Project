"""
core/models.py — Production models re-export.

Imports all Pydantic models from backend/models.py so production code can use:
    from core.models import BreachEvent, AlertOut, ...
"""

from models import (  # noqa: F401
    BreachEvent,
    ReadingOut,
    AlertOut,
    SubscriberIn,
    SubscriberOut,
    PushSubscriptionIn,
    ThresholdConfigIn,
    ThresholdConfigOut,
    ThresholdConfigDetailOut,
    AcknowledgeIn,
    DeliveryReceiptOut,
    ConfigChangeOut,
)
