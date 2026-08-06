"""Async MongoDB connection management using Motor."""

from __future__ import annotations

import asyncio

import motor.motor_asyncio
from motor.core import AgnosticClient, AgnosticDatabase

from config.config import settings
from utils.logging_setup import get_logger

logger = get_logger("database.connection")

_client: AgnosticClient | None = None
_db: AgnosticDatabase | None = None


async def connect_to_mongo() -> AgnosticDatabase:
    """Connect to MongoDB.

    Returns:
        AgnosticDatabase: Database instance.

    Raises:
        ConnectionError: If connection fails after retries.
    """
    global _client, _db

    if _db is not None:
        return _db

    attempts = 0
    max_attempts = 5
    delay = 1.0

    while attempts < max_attempts:
        try:
            logger.info("Connecting to MongoDB", uri=settings.MONGO_URI, attempt=attempts + 1)
            _client = motor.motor_asyncio.AsyncIOMotorClient(
                settings.MONGO_URI,
                maxPoolSize=50,
                minPoolSize=5,
                serverSelectionTimeoutMS=10000,
                socketTimeoutMS=10000,
                connectTimeoutMS=10000,
                retryWrites=True,
            )
            _db = _client[settings.MONGO_DB_NAME]
            await _db.command("ping")
            logger.info("MongoDB connected successfully", db_name=settings.MONGO_DB_NAME)
            return _db
        except Exception as exc:
            attempts += 1
            logger.error(
                "MongoDB connection failed",
                error=str(exc),
                attempt=attempts,
                max_attempts=max_attempts,
            )
            if attempts >= max_attempts:
                logger.critical("MongoDB connection failed after max retries")
                raise ConnectionError(
                    f"Failed to connect to MongoDB after {max_attempts} attempts: {exc}"
                )
            delay *= 2
            await asyncio.sleep(delay)

    raise ConnectionError("Failed to connect to MongoDB")


async def reconnect_to_mongo() -> AgnosticDatabase:
    """Reconnect to MongoDB.

    Returns:
        AgnosticDatabase: Database instance.
    """
    global _client, _db

    _client = None
    _db = None

    if _client is not None:
        _client.close()

    return await connect_to_mongo()


async def close_mongo() -> None:
    """Close the MongoDB connection."""
    global _client, _db
    if _client is not None:
        _client.close()
        _client = None
        _db = None
        logger.info("MongoDB connection closed")


def get_db() -> AgnosticDatabase:
    """Get the database instance.

    Returns:
        AgnosticDatabase: Database instance.

    Raises:
        RuntimeError: If database is not connected.
    """
    if _db is None:
        raise RuntimeError("Database not connected. Call connect_to_mongo() first.")
    return _db


def get_collection(collection_name: str):
    """Get a MongoDB collection by name.

    Args:
        collection_name: Name of the collection.

    Returns:
        Collection instance.
    """
    return get_db()[collection_name]
