"""
models.py — Pydantic v2 request/response models for SentinelEdge API.
"""

from __future__ import annotations
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class BreachEvent(BaseModel):
    parameter: str
    value: float
    threshold: float
    direction: str          # "high" | "low"
    severity: str = "WARNING"  # "WARNING" | "CRITICAL" | "EMERGENCY" (Addition 2)


class ReadingOut(BaseModel):
    temperature: float
    humidity: float
    timestamp: str
    breaches: list[BreachEvent] = Field(default_factory=list)
    is_valid: bool = True   # Addition 3: False when validator rejects reading


class AlertOut(BaseModel):
    id: int
    parameter: str
    value: float
    threshold: float
    direction: str
    severity: str = "WARNING"   # Addition 2
    timestamp: str
    acknowledged: bool
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[str] = None
    escalation_level: int
    max_escalated: bool
    cooldown_until: Optional[str] = None
    delivery_status: Optional[Dict[str, str]] = None  # Addition 4


class SubscriberIn(BaseModel):
    name: str
    phone: str
    email: str
    escalation_order: int = Field(ge=1, le=10)


class SubscriberOut(BaseModel):
    id: int
    name: str
    phone: str
    email: str
    escalation_order: int
    active: bool
    has_push_subscription: bool
    created_at: str


class PushSubscriptionIn(BaseModel):
    subscription_json: str


class ThresholdConfigIn(BaseModel):
    temp_high: float
    temp_low: float
    humidity_high: float
    humidity_low: float


class ThresholdConfigOut(BaseModel):
    temp_high: float
    temp_low: float
    humidity_high: float
    humidity_low: float


class ThresholdConfigDetailOut(BaseModel):
    """Extended threshold response with source tracking (Addition 11)."""
    temperature: Dict[str, Any]
    humidity: Dict[str, Any]
    source: str
    last_changed: str


class AcknowledgeIn(BaseModel):
    acknowledged_by: str


class DeliveryReceiptOut(BaseModel):
    """Single delivery receipt (Addition 4)."""
    id: int
    alert_id: int
    channel: str
    subscriber_id: int
    escalation_level: int
    sent_at: str
    success: bool
    error_message: Optional[str] = None


class ConfigChangeOut(BaseModel):
    """Config audit log entry (Addition 6)."""
    id: int
    changed_by: str
    field_name: str
    old_value: str
    new_value: str
    changed_at: str
