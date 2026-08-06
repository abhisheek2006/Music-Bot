"""Constants used across the application."""

from __future__ import annotations

from enum import StrEnum


class Callbacks(StrEnum):
    """Callback query data patterns for inline keyboards."""

    # Main menu
    MENU_SEARCH = "menu:search"
    MENU_HISTORY = "menu:history"
    MENU_CREDITS = "menu:credits"
    MENU_HELP = "menu:help"
    MENU_UPDATES = "menu:updates"
    MENU_PROFILE = "menu:profile"
    MENU_BACK = "menu:back"
    MENU_CLOSE = "menu:close"

    # Search
    SEARCH_START = "search:start"
    SEARCH_CANCEL = "search:cancel"

    # History pagination
    HISTORY_PAGE = "history:page"

    # Admin panel
    ADMIN_PANEL = "admin:panel"
    ADMIN_USERS = "admin:users"
    ADMIN_CREDITS = "admin:credits"
    ADMIN_BROADCAST = "admin:broadcast"
    ADMIN_STATS = "admin:stats"
    ADMIN_SEARCH_LOGS = "admin:search_logs"
    ADMIN_BANS = "admin:bans"
    ADMIN_FORCE_JOIN = "admin:force_join"
    ADMIN_MAINTENANCE = "admin:maintenance"
    ADMIN_API_STATUS = "admin:api_status"
    ADMIN_RESTART = "admin:restart"
    ADMIN_SHUTDOWN = "admin:shutdown"
    ADMIN_EXPORT_DB = "admin:export_db"
    ADMIN_EXPORT_LOGS = "admin:export_logs"

    # Admin sub-actions
    ADMIN_USER_DETAIL = "admin:user_detail"
    ADMIN_USER_BAN = "admin:user_ban"
    ADMIN_USER_UNBAN = "admin:user_unban"
    ADMIN_USER_CREDITS = "admin:user_credits"
    ADMIN_BROADCAST_SEND = "admin:broadcast_send"
    ADMIN_BROADCAST_CANCEL = "admin:broadcast_cancel"
    ADMIN_EXPORT_TYPE = "admin:export_type"
    ADMIN_EXPORT_FORMAT = "admin:export_format"
    ADMIN_CONFIRM = "admin:confirm"
    ADMIN_CANCEL = "admin:cancel"

    # Force join
    ADMIN_FORCE_JOIN_TOGGLE = "admin:force_join_toggle"
    ADMIN_FORCE_JOIN_SET = "admin:force_join_set"

    # Pagination
    ADMIN_USERS_PAGE = "admin:users_page"
    ADMIN_BANS_PAGE = "admin:bans_page"
    ADMIN_STATS_PERIOD = "admin:stats_period"


class RegexPatterns:
    """Regex patterns for input validation."""

    PHONE_NUMBER = r"^[\+]?[1-9][\d]{0,15}$"
    USER_ID = r"^\d+$"
    CREDIT_AMOUNT = r"^-?\d+$"
    EMAIL = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"


class LogMessages:
    """Standardized log message templates."""

    USER_STARTED = "User started the bot"
    SEARCH_PERFORMED = "Search performed"
    CREDIT_DEDUCTED = "Credit deducted"
    CREDIT_ADDED = "Credit added"
    CREDIT_REMOVED = "Credit removed"
    CREDIT_SET = "Credit set"
    ADMIN_ACTION = "Admin action performed"
    BROADCAST_SENT = "Broadcast message sent"
    COMMAND_EXECUTED = "Command executed"
    ERROR_OCCURRED = "Error occurred"
    USER_BANNED = "User banned"
    USER_UNBANNED = "User unbanned"


class Messages:
    """Common text messages used by the bot."""

    ADMIN_ONLY = "❌ This command is for administrators only."
    NOT_ADMIN = "❌ You are not an administrator."
    NO_CREDITS = (
        "❌ You don't have enough credits to perform a search.\n\n"
        "Each search costs 1 credit.\n"
        "Contact an administrator to add credits."
    )
    SEARCH_NOT_AVAILABLE = (
        "🔍 Search feature is temporarily unavailable. Please try again later or contact support."
    )
    INVALID_INPUT = "❌ Invalid input. Please try again."
    CANCELLED = "✅ Operation cancelled."
    PROCESSING = "⏳ Processing... Please wait."
    NO_HISTORY = "📜 You don't have any search history yet."
    NO_BROADCAST = "📭 You haven't received any broadcasts."
    NO_UPDATES = "📢 No new updates available."
    BOT_RESTARTING = "🔄 Restarting the bot..."
    BOT_SHUTTING_DOWN = "🛑 Shutting down the bot..."
    MAINTENANCE_ENABLED = "🔧 Maintenance mode has been enabled."
    MAINTENANCE_DISABLED = "🔓 Maintenance mode has been disabled."
    NO_BANS = "✅ No banned users."
    NO_ADMINS = "❌ No admin users found in the database."
    OPERATION_FAILED = "❌ Operation failed. Please try again."
    OPERATION_SUCCESS = "✅ Operation completed successfully."
    USER_NOT_FOUND = "❌ User not found."
    INVALID_USER_ID = "❌ Invalid user ID."
    INVALID_CREDIT_AMOUNT = "❌ Invalid credit amount."
    CREDIT_LOG_EMPTY = "📜 No credit transactions found."
    INVALID_EXPORT_FORMAT = "❌ Invalid export format."
    EXPORT_STARTED = "📊 Export started. Please wait..."
    EXPORT_COMPLETED = "✅ Export completed."
    EXPORT_FAILED = "❌ Export failed."
    NO_SEARCH_LOGS = "📜 No search logs found."
    NO_STATS = "📊 No statistics available."
    DB_RECONNECTED = "✅ Database reconnected successfully."
    DB_DISCONNECTED = "⚠️ Database disconnected."
    BOT_RECONNECTED = "✅ Bot reconnected successfully."
    GRACEFUL_SHUTDOWN = "🛑 Graceful shutdown initiated..."
    HEALTH_OK = "healthy"
    NO_CHANNEL_SET = "⚠️ No force-join channel is configured."
    CHANNEL_SET = "✅ Force-join channel set to: {channel}"
    CHANNEL_CLEARED = "✅ Force-join channel cleared."
    MUST_JOIN = (
        "⚠️ You must join our channel to use this bot:\n{channel}\n\n"
        "Click the button below after joining."
    )


class Statuses(StrEnum):
    """Document statuses."""

    ACTIVE = "active"
    BANNED = "banned"
    DELETED = "deleted"

    SEARCH_SUCCESS = "success"
    SEARCH_FAILED = "failed"
    SEARCH_NO_RESULTS = "no_results"

    CREDIT_ADDED = "added"
    CREDIT_REMOVED = "removed"
    CREDIT_SET = "set"
    CREDIT_DEDUCTED = "deducted"

    BROADCAST_SENT = "sent"
    BROADCAST_FAILED = "failed"
    BROADCAST_COMPLETED = "completed"
