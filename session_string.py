from __future__ import annotations

import asyncio

from pyrogram import Client


async def main() -> None:
    api_id = (await asyncio.to_thread(input, "API ID: ")).strip()
    api_hash = (await asyncio.to_thread(input, "API HASH: ")).strip()
    if not api_id.isdigit():
        print("API ID must be a number.")
        return
    session_name = (
        await asyncio.to_thread(input, "Session name [music_user]: ")
    ).strip() or "music_user"

    app = Client(
        session_name,
        api_id=int(api_id),
        api_hash=api_hash,
        in_memory=True,
    )
    await app.start()
    me = await app.get_me()
    print(f"\nLogged in as {me.first_name} (@{me.username})")
    session_string = await app.export_session_string()
    print("\nYour SESSION_STRING (keep it secret):\n")
    print(session_string)
    print()
    await app.stop()


if __name__ == "__main__":
    asyncio.run(main())
