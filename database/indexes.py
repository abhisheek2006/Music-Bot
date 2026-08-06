"""MongoDB index creation for all collections."""

from __future__ import annotations

from motor.core import AgnosticDatabase

from utils.logging_setup import get_logger

logger = get_logger("database.indexes")


async def create_indexes(db: AgnosticDatabase) -> None:
    """Create indexes for all collections.

    Args:
        db: Database instance.
    """
    await _create_users_indexes(db)
    await _create_searches_indexes(db)
    await _create_credit_logs_indexes(db)
    await _create_broadcasts_indexes(db)
    await _create_settings_indexes(db)
    await _create_admins_indexes(db)
    await _create_bans_indexes(db)
    await _create_statistics_indexes(db)
    logger.info("All indexes created successfully")


async def _create_users_indexes(db: AgnosticDatabase) -> None:
    """Create indexes for the users collection."""
    collection = db["users"]
    await collection.create_index("user_id", unique=True)
    await collection.create_index([("created_at", 1)])
    await collection.create_index("is_admin", sparse=True)
    await collection.create_index("banned", sparse=True)
    await collection.create_index("username")
    logger.debug("Users indexes created")


async def _create_searches_indexes(db: AgnosticDatabase) -> None:
    """Create indexes for the searches collection."""
    collection = db["searches"]
    await collection.create_index("user_id", 1)
    await collection.create_index([("user_id", 1), ("timestamp", -1)])
    await collection.create_index("timestamp", 1)
    await collection.create_index("query")
    logger.debug("Searches indexes created")


async def _create_credit_logs_indexes(db: AgnosticDatabase) -> None:
    """Create indexes for the credit_logs collection."""
    collection = db["credit_logs"]
    await collection.create_index("user_id", 1)
    await collection.create_index([("user_id", 1), ("timestamp", -1)])
    await collection.create_index("timestamp", 1)
    await collection.create_index("admin_id")
    logger.debug("Credit logs indexes created")


async def _create_broadcasts_indexes(db: AgnosticDatabase) -> None:
    """Create indexes for the broadcasts collection."""
    collection = db["broadcasts"]
    await collection.create_index([("created_at", -1)])
    await collection.create_index("status")
    await collection.create_index("recipient_count")
    logger.debug("Broadcasts indexes created")


async def _create_settings_indexes(db: AgnosticDatabase) -> None:
    """Create indexes for the settings collection."""
    collection = db["settings"]
    await collection.create_index("key", unique=True)
    logger.debug("Settings indexes created")


async def _create_admins_indexes(db: AgnosticDatabase) -> None:
    """Create indexes for the admins collection."""
    collection = db["admins"]
    await collection.create_index("user_id", unique=True)
    await collection.create_index("role")
    logger.debug("Admins indexes created")


async def _create_bans_indexes(db: AgnosticDatabase) -> None:
    """Create indexes for the bans collection."""
    collection = db["bans"]
    await collection.create_index("user_id", unique=True)
    await collection.create_index("banned_at")
    logger.debug("Bans indexes created")


async def _create_statistics_indexes(db: AgnosticDatabase) -> None:
    """Create indexes for the statistics collection."""
    collection = db["statistics"]
    await collection.create_index([("date", 1), ("type", 1)], unique=True)
    await collection.create_index("date")
    logger.debug("Statistics indexes created")
