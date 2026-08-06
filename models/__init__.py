"""Data models for the Telebot application."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class User(BaseModel):
    """User model."""

    model_config = ConfigDict(use_enum_values=True)

    COLLECTION: str = "users"

    user_id: int
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    is_admin: bool = False
    credits: int = 0
    banned: bool = False
    referrer_id: int | None = None
    referral_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    language_code: str | None = None


class Search(BaseModel):
    """Search log model."""

    model_config = ConfigDict(use_enum_values=True)

    COLLECTION: str = "searches"

    user_id: int
    query: str
    result: str | None = None
    success: bool = False
    ip_address: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    duration_ms: int | None = None


class CreditTransaction(BaseModel):
    """Credit transaction model."""

    model_config = ConfigDict(use_enum_values=True)

    COLLECTION: str = "credit_logs"

    user_id: int
    admin_id: int
    amount: int
    action: str
    reason: str | None = None
    balance_after: int
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Broadcast(BaseModel):
    """Broadcast message model."""

    model_config = ConfigDict(use_enum_values=True)

    COLLECTION: str = "broadcasts"

    admin_id: int
    message: str
    status: str = "pending"
    recipient_count: int = 0
    error_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None


class Setting(BaseModel):
    """Bot setting model."""

    model_config = ConfigDict(use_enum_values=True)

    COLLECTION: str = "settings"

    key: str
    value: str


class AdminAction(BaseModel):
    """Admin action log model."""

    model_config = ConfigDict(use_enum_values=True)

    COLLECTION: str = "admin_logs"

    admin_id: int
    action: str
    target_id: int | None = None
    details: dict[str, Any] | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Ban(BaseModel):
    """Ban model."""

    model_config = ConfigDict(use_enum_values=True)

    COLLECTION: str = "bans"

    user_id: int
    admin_id: int
    reason: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DailyStat(BaseModel):
    """Daily statistics model."""

    model_config = ConfigDict(use_enum_values=True)

    COLLECTION: str = "statistics"

    date: str
    type: str
    value: int = 0
    details: dict[str, Any] | None = None
