"""
models.py — Pydantic v2 request/response models for SentinelEdge API.

All input models include field_validator declarations that:
- Strip whitespace from string fields.
- Enforce business constraints with clear error messages.
- Return HTTP 422 automatically on failure (Pydantic handles it).
"""

from __future__ import annotations

import re
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field, field_validator, model_validator, EmailStr


# ── Domain events ─────────────────────────────────────────────────────────────

class BreachEvent(BaseModel):
    parameter: str
    value: float
    threshold: float
    direction: str          # "high" | "low"
    severity: str = "WARNING"   # "WARNING" | "CRITICAL" | "EMERGENCY"


# ── API response models ───────────────────────────────────────────────────────

class ReadingOut(BaseModel):
    temperature: float
    timestamp: str
    breaches: list[BreachEvent] = Field(default_factory=list)
    is_valid: bool = True


class AlertOut(BaseModel):
    id: int
    parameter: str
    value: float
    threshold: float
    direction: str
    severity: str = "WARNING"
    timestamp: str
    acknowledged: bool
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[str] = None
    escalation_level: int
    max_escalated: bool
    cooldown_until: Optional[str] = None
    delivery_status: Optional[Dict[str, str]] = None


# ── Input models with validation ──────────────────────────────────────────────

class SubscriberIn(BaseModel):
    name: str
    phone: str
    email: EmailStr
    escalation_order: int = Field(ge=1, le=9999)
    pin: Optional[str] = None  # if provided: 4-6 digits, stored as SHA-256 hash

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("name must be at least 2 characters")
        if len(v) > 50:
            raise ValueError("name must be at most 50 characters")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r"^\+?[0-9]{10,15}$", v):
            raise ValueError(
                "phone must be 10-15 digits, optionally prefixed with +"
            )
        return v

    @field_validator("pin")
    @classmethod
    def validate_pin(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not re.match(r"^[0-9]{4,6}$", v):
            raise ValueError("pin must be 4-6 digits (numbers only)")
        return v


class SubscriberOut(BaseModel):
    id: int
    name: str
    phone: str
    email: str
    escalation_order: int
    active: bool
    has_pin: bool
    created_at: str


class PushSubscriptionIn(BaseModel):
    subscription_json: str


class ThresholdConfigIn(BaseModel):
    temp_high: float
    temp_low: float

    @field_validator("temp_high")
    @classmethod
    def validate_temp_high(cls, v: float) -> float:
        if not (-50.0 <= v <= 150.0):
            raise ValueError("temp_high must be between -50 and 150")
        return v

    @field_validator("temp_low")
    @classmethod
    def validate_temp_low(cls, v: float) -> float:
        if not (-50.0 <= v <= 150.0):
            raise ValueError("temp_low must be between -50 and 150")
        return v

    @model_validator(mode="after")
    def validate_high_gt_low(self) -> "ThresholdConfigIn":
        if self.temp_high <= self.temp_low:
            raise ValueError(
                f"temp_high ({self.temp_high}) must be greater than "
                f"temp_low ({self.temp_low})"
            )
        return self


class ThresholdConfigOut(BaseModel):
    temp_high: float
    temp_low: float


class ThresholdConfigDetailOut(BaseModel):
    """Extended threshold response with source tracking."""
    temperature: Dict[str, Any]
    source: str
    last_changed: str


class AcknowledgeIn(BaseModel):
    acknowledged_by: str

    @field_validator("acknowledged_by")
    @classmethod
    def validate_acknowledged_by(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError(
                "acknowledged_by must be at least 2 characters and cannot be empty"
            )
        if len(v) > 50:
            raise ValueError("acknowledged_by must be at most 50 characters")
        return v


class DeliveryReceiptOut(BaseModel):
    """Single delivery receipt."""
    id: int
    alert_id: int
    channel: str
    subscriber_id: int
    escalation_level: int
    sent_at: str
    success: bool
    error_message: Optional[str] = None


class ConfigChangeOut(BaseModel):
    """Config audit log entry."""
    id: int
    changed_by: str
    field_name: str
    old_value: str
    new_value: str
    changed_at: str


# ── Auth models ───────────────────────────────────────────────────────────────

class LoginIn(BaseModel):
    """Mobile app login request: name + numeric PIN."""
    name: str
    pin: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("name must be at least 2 characters")
        return v

    @field_validator("pin")
    @classmethod
    def validate_pin(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r"^[0-9]{4,6}$", v):
            raise ValueError("pin must be 4-6 digits (numbers only)")
        return v


class LoginOut(BaseModel):
    """Successful login response."""
    token: str
    subscriber_id: int
    name: str
    escalation_order: int
    message: str = "Login successful"


class SetPinIn(BaseModel):
    """Admin request to set or update a subscriber's PIN."""
    subscriber_id: int
    pin: str

    @field_validator("pin")
    @classmethod
    def validate_pin(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r"^[0-9]{4,6}$", v):
            raise ValueError("pin must be 4-6 digits (numbers only)")
        return v
