"""Inline keyboard builders for the bot."""

from __future__ import annotations

from kurigram import InlineKeyboardButton, InlineKeyboardMarkup, enums

ButtonStyle = enums.ButtonStyle

RED = ButtonStyle.DANGER
GREEN = ButtonStyle.SUCCESS
BLUE = ButtonStyle.PRIMARY
DEFAULT = ButtonStyle.DEFAULT


class KeyboardBuilder:
    """Builder class for inline keyboards."""

    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        """Build the main user menu keyboard."""
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🔍 Search Number", callback_data="menu:search", style=BLUE
                    ),
                    InlineKeyboardButton("📜 History", callback_data="menu:history"),
                ],
                [
                    InlineKeyboardButton("💳 My Credits", callback_data="menu:credits"),
                    InlineKeyboardButton("ℹ️ Help", callback_data="menu:help"),
                ],
                [
                    InlineKeyboardButton("📢 Updates", callback_data="menu:updates"),
                    InlineKeyboardButton("👤 Profile", callback_data="menu:profile"),
                ],
            ]
        )

    @staticmethod
    def admin_menu() -> InlineKeyboardMarkup:
        """Build the admin panel keyboard."""
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "👥 User Management", callback_data="admin:users", style=BLUE
                    ),
                    InlineKeyboardButton(
                        "💳 Credit Management", callback_data="admin:credits", style=GREEN
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "📢 Broadcast", callback_data="admin:broadcast", style=BLUE
                    ),
                    InlineKeyboardButton(
                        "🎨 Designer", callback_data="admin:broadcast_d", style=GREEN
                    ),
                ],
                [
                    InlineKeyboardButton("📜 Search Logs", callback_data="admin:search_logs"),
                    InlineKeyboardButton("🔨 Ban/Unban", callback_data="admin:bans", style=RED),
                ],
                [
                    InlineKeyboardButton("🔗 Force Join", callback_data="admin:force_join"),
                    InlineKeyboardButton("🔧 Maintenance", callback_data="admin:maintenance"),
                ],
                [
                    InlineKeyboardButton("📊 Statistics", callback_data="admin:stats"),
                ],
                [
                    InlineKeyboardButton(
                        "🔄 Restart Bot", callback_data="admin:restart", style=RED
                    ),
                    InlineKeyboardButton(
                        "🛑 Shutdown Bot", callback_data="admin:shutdown", style=RED
                    ),
                ],
                [
                    InlineKeyboardButton("📥 Export DB", callback_data="admin:export_db"),
                    InlineKeyboardButton("📋 Export Logs", callback_data="admin:export_logs"),
                ],
                [
                    InlineKeyboardButton("🔙 Back", callback_data="menu:back"),
                ],
            ]
        )

    @staticmethod
    def back_to_main() -> InlineKeyboardMarkup:
        """Build a back-to-main-menu keyboard."""
        return InlineKeyboardMarkup([InlineKeyboardButton("🔙 Back", callback_data="menu:back")])

    @staticmethod
    def back_to_admin() -> InlineKeyboardMarkup:
        """Build a back-to-admin-panel keyboard."""
        return InlineKeyboardMarkup(
            [InlineKeyboardButton("🔙 Back to Admin", callback_data="admin:panel")]
        )

    @staticmethod
    def cancel_button() -> InlineKeyboardMarkup:
        """Build a cancel keyboard."""
        return InlineKeyboardMarkup(
            [InlineKeyboardButton("❌ Cancel", callback_data="menu:close", style=RED)]
        )

    @staticmethod
    def history_pagination(
        total: int,
        current_page: int,
        page_size: int = 10,
    ) -> InlineKeyboardMarkup:
        """Build pagination keyboard for history.

        Args:
            total: Total number of records.
            current_page: Current page number (0-indexed).
            page_size: Records per page.

        Returns:
            InlineKeyboardMarkup.
        """
        buttons: list[list[InlineKeyboardButton]] = []
        nav_buttons: list[InlineKeyboardButton] = []

        total_pages = max(1, (total + page_size - 1) // page_size)

        if current_page > 0:
            prev_data = f"history:page:{current_page - 1}"
            nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=prev_data))

        nav_buttons.append(
            InlineKeyboardButton(
                f"📄 {current_page + 1}/{total_pages}",
                callback_data="history:noop",
            )
        )

        if current_page < total_pages - 1:
            next_data = f"history:page:{current_page + 1}"
            nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=next_data))

        if nav_buttons:
            buttons.append(nav_buttons)

        buttons.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="menu:back")])

        return InlineKeyboardMarkup(buttons)

    @staticmethod
    def admin_users_pagination(
        total: int,
        current_page: int,
        page_size: int = 10,
    ) -> InlineKeyboardMarkup:
        """Build pagination keyboard for admin user list."""
        buttons: list[list[InlineKeyboardButton]] = []
        nav_buttons: list[InlineKeyboardButton] = []

        total_pages = max(1, (total + page_size - 1) // page_size)

        if current_page > 0:
            nav_buttons.append(
                InlineKeyboardButton(
                    "⬅️ Previous",
                    callback_data=f"admin:users_page:{current_page - 1}",
                )
            )

        nav_buttons.append(
            InlineKeyboardButton(
                f"📄 {current_page + 1}/{total_pages}",
                callback_data="admin:noop",
            )
        )

        if current_page < total_pages - 1:
            nav_buttons.append(
                InlineKeyboardButton(
                    "Next ➡️",
                    callback_data=f"admin:users_page:{current_page + 1}",
                )
            )

        if nav_buttons:
            buttons.append(nav_buttons)

        buttons.append([InlineKeyboardButton("🔙 Back to Admin", callback_data="admin:panel")])

        return InlineKeyboardMarkup(buttons)

    @staticmethod
    def admin_bans_pagination(
        total: int,
        current_page: int,
        page_size: int = 10,
    ) -> InlineKeyboardMarkup:
        """Build pagination keyboard for admin ban list."""
        buttons: list[list[InlineKeyboardButton]] = []
        nav_buttons: list[InlineKeyboardButton] = []

        total_pages = max(1, (total + page_size - 1) // page_size)

        if current_page > 0:
            nav_buttons.append(
                InlineKeyboardButton(
                    "⬅️ Previous",
                    callback_data=f"admin:bans_page:{current_page - 1}",
                )
            )

        nav_buttons.append(
            InlineKeyboardButton(
                f"📄 {current_page + 1}/{total_pages}",
                callback_data="admin:noop",
            )
        )

        if current_page < total_pages - 1:
            nav_buttons.append(
                InlineKeyboardButton(
                    "Next ➡️",
                    callback_data=f"admin:bans_page:{current_page + 1}",
                )
            )

        if nav_buttons:
            buttons.append(nav_buttons)

        buttons.append([InlineKeyboardButton("🔙 Back to Admin", callback_data="admin:panel")])

        return InlineKeyboardMarkup(buttons)

    @staticmethod
    def admin_search_logs_pagination(
        total: int,
        current_page: int,
        page_size: int = 10,
    ) -> InlineKeyboardMarkup:
        """Build pagination keyboard for admin search logs."""
        buttons: list[list[InlineKeyboardButton]] = []
        nav_buttons: list[InlineKeyboardButton] = []

        total_pages = max(1, (total + page_size - 1) // page_size)

        if current_page > 0:
            nav_buttons.append(
                InlineKeyboardButton(
                    "⬅️ Previous",
                    callback_data=f"admin:search_logs_page:{current_page - 1}",
                )
            )

        nav_buttons.append(
            InlineKeyboardButton(
                f"📄 {current_page + 1}/{total_pages}",
                callback_data="admin:noop",
            )
        )

        if current_page < total_pages - 1:
            nav_buttons.append(
                InlineKeyboardButton(
                    "Next ➡️",
                    callback_data=f"admin:search_logs_page:{current_page + 1}",
                )
            )

        if nav_buttons:
            buttons.append(nav_buttons)

        buttons.append([InlineKeyboardButton("🔙 Back to Admin", callback_data="admin:panel")])

        return InlineKeyboardMarkup(buttons)

    @staticmethod
    def user_detail_actions(user_id: int) -> InlineKeyboardMarkup:
        """Build user detail action keyboard for admin.

        Args:
            user_id: User ID.

        Returns:
            InlineKeyboardMarkup.
        """
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "💳 Add Credit",
                        callback_data=f"admin:user_credits:{user_id}:add",
                        style=GREEN,
                    ),
                    InlineKeyboardButton(
                        "➖ Remove Credit",
                        callback_data=f"admin:user_credits:{user_id}:remove",
                        style=RED,
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "🚫 Ban",
                        callback_data=f"admin:user_ban:{user_id}",
                        style=RED,
                    ),
                    InlineKeyboardButton(
                        "✅ Unban",
                        callback_data=f"admin:user_unban:{user_id}",
                        style=GREEN,
                    ),
                    InlineKeyboardButton(
                        "🗑️ Delete",
                        callback_data=f"admin:user_delete:{user_id}",
                        style=RED,
                    ),
                ],
                [InlineKeyboardButton("🔙 Back", callback_data="admin:users")],
            ]
        )

    @staticmethod
    def single_button(text: str, callback_data: str) -> InlineKeyboardMarkup:
        """Build a keyboard with a single button.

        Args:
            text: Button text.
            callback_data: Callback data.

        Returns:
            InlineKeyboardMarkup.
        """
        return InlineKeyboardMarkup([InlineKeyboardButton(text, callback_data=callback_data)])

    @staticmethod
    def force_join_confirm(url: str) -> InlineKeyboardMarkup:
        """Build force-join confirmation keyboard.

        Args:
            url: Channel join URL.

        Returns:
            InlineKeyboardMarkup.
        """
        return InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🔗 Join Channel", url=url, style=BLUE)],
                [InlineKeyboardButton("✅ Joined", callback_data="force_join:done", style=GREEN)],
            ]
        )

    @staticmethod
    def yes_no(
        yes_data: str = "confirm:yes",
        no_data: str = "confirm:no",
    ) -> InlineKeyboardMarkup:
        """Build a yes/no confirmation keyboard.

        Args:
            yes_data: Callback data for yes.
            no_data: Callback data for no.

        Returns:
            InlineKeyboardMarkup.
        """
        return InlineKeyboardMarkup(
            [
                InlineKeyboardButton("✅ Yes", callback_data=yes_data, style=GREEN),
                InlineKeyboardButton("❌ No", callback_data=no_data, style=RED),
            ]
        )

    @staticmethod
    def stats_period_selector() -> InlineKeyboardMarkup:
        """Build statistics period selector keyboard."""
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "📊 Daily", callback_data="admin:stats_period:daily", style=BLUE
                    ),
                    InlineKeyboardButton("📅 Weekly", callback_data="admin:stats_period:weekly"),
                ],
                [
                    InlineKeyboardButton("📆 Monthly", callback_data="admin:stats_period:monthly"),
                    InlineKeyboardButton("🌍 Global", callback_data="admin:stats_period:global"),
                ],
                [InlineKeyboardButton("🔙 Back", callback_data="admin:panel")],
            ]
        )

    @staticmethod
    def export_format_selector(export_type: str = "db") -> InlineKeyboardMarkup:
        """Build export format selector keyboard.

        Args:
            export_type: Type of export (db or logs).

        Returns:
            InlineKeyboardMarkup.
        """
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "📄 JSON", callback_data=f"admin:export_format:json:{export_type}"
                    ),
                    InlineKeyboardButton(
                        "📊 CSV", callback_data=f"admin:export_format:csv:{export_type}"
                    ),
                ],
                [InlineKeyboardButton("🔙 Back", callback_data="admin:panel")],
            ]
        )

    @staticmethod
    def close_button() -> InlineKeyboardMarkup:
        """Build a close keyboard."""
        return InlineKeyboardMarkup(
            [InlineKeyboardButton("❌ Close", callback_data="menu:close", style=RED)]
        )


keyboards = KeyboardBuilder
