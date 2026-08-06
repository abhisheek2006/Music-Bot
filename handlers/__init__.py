"""Handlers package - registers all command and callback handlers."""

from __future__ import annotations

from kurigram import AsyncClient

import handlers.admin_commands
import handlers.admin_panel
import handlers.credits
import handlers.force_join
import handlers.help
import handlers.history
import handlers.profile
import handlers.search
import handlers.start
import handlers.updates
import handlers.welcome


def register_all_handlers(client: AsyncClient) -> None:
    """Register all handlers with the client.

    Args:
        client: Kurigram client instance.
    """
    handlers.start.register_handlers(client)
    handlers.help.register_handlers(client)
    handlers.search.register_handlers(client)
    handlers.history.register_handlers(client)
    handlers.credits.register_handlers(client)
    handlers.profile.register_handlers(client)
    handlers.updates.register_handlers(client)
    handlers.welcome.register_handlers(client)
    handlers.force_join.register_handlers(client)
    handlers.admin_commands.register_handlers(client)
    handlers.admin_panel.register_handlers(client)
