"""Database repositories package."""

from __future__ import annotations

from database.repositories.admin_repo import admin_repo
from database.repositories.ban_repo import ban_repo
from database.repositories.broadcast_repo import broadcast_repo
from database.repositories.credit_log_repo import credit_log_repo
from database.repositories.credit_repo import credit_repo
from database.repositories.search_repo import search_repo
from database.repositories.setting_repo import setting_repo
from database.repositories.statistics_repo import statistics_repo
from database.repositories.user_repo import user_repo

__all__ = [
    "user_repo",
    "search_repo",
    "credit_repo",
    "credit_log_repo",
    "broadcast_repo",
    "setting_repo",
    "admin_repo",
    "ban_repo",
    "statistics_repo",
]
