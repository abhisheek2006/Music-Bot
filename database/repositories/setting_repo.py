"""Settings repository for MongoDB operations."""

from __future__ import annotations

from motor.core import AgnosticCollection

from database.connection import get_collection
from utils.logging_setup import get_logger

logger = get_logger("database.setting_repo")


class SettingRepository:
    """Repository for bot settings operations."""

    def __init__(self) -> None:
        self._collection_name = "settings"

    @property
    def collection(self) -> AgnosticCollection:
        """Get the settings collection."""
        return get_collection(self._collection_name)

    async def get(self, key: str) -> str | None:
        """Get a setting value by key.

        Args:
            key: Setting key.

        Returns:
            Setting value or None.
        """
        doc = await self.collection.find_one({"key": key}, {"_id": 0, "value": 1})
        if doc:
            return doc.get("value")
        return None

    async def get_bool(self, key: str, default: bool = False) -> bool:
        """Get a boolean setting value.

        Args:
            key: Setting key.
            default: Default value.

        Returns:
            Boolean value.
        """
        value = await self.get(key)
        if value is None:
            return default
        return value.lower() in ("true", "1", "yes", "on")

    async def set(self, key: str, value: str) -> None:
        """Set a setting value.

        Args:
            key: Setting key.
            value: Setting value.
        """
        await self.collection.find_one_and_update(
            {"key": key},
            {"$set": {"value": value}},
            upsert=True,
        )
        logger.debug("Setting updated", key=key)

    async def set_bool(self, key: str, value: bool) -> None:
        """Set a boolean setting value.

        Args:
            key: Setting key.
            value: Boolean value.
        """
        await self.set(key, str(value).lower())

    async def get_maintenance_mode(self) -> bool:
        """Check if maintenance mode is enabled.

        Returns:
            True if maintenance mode is on.
        """
        env_mode = None
        try:
            from config.config import settings

            env_mode = settings.MAINTENANCE_MODE
        except Exception:
            pass

        db_mode = await self.get_bool("maintenance_mode", default=False)
        return env_mode or db_mode

    async def set_maintenance_mode(self, enabled: bool) -> None:
        """Set maintenance mode.

        Args:
            enabled: Whether to enable maintenance mode.
        """
        await self.set_bool("maintenance_mode", enabled)

    async def get_force_join_channel(self) -> str | None:
        """Get the force-join channel.

        Returns:
            Channel username or None.
        """
        return await self.get("force_join_channel")

    async def set_force_join_channel(self, channel: str | None) -> None:
        """Set the force-join channel.

        Args:
            channel: Channel username or None to clear.
        """
        if channel:
            await self.set("force_join_channel", channel)
        else:
            await self.collection.delete_one({"key": "force_join_channel"})


setting_repo = SettingRepository()
