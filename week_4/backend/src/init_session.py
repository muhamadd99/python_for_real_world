"""One-time Telegram session initializer.

Usage (inside Docker):
    docker compose run --rm userbot python -m src.init_session

Or locally:
    python -m src.init_session
"""

from __future__ import annotations

import asyncio
import os
from dotenv import load_dotenv
from telethon import TelegramClient


async def main() -> None:
    load_dotenv()

    api_id = int(os.environ["TELEGRAM_API_ID"])
    api_hash = os.environ["TELEGRAM_API_HASH"]
    session_name = os.getenv("TELEGRAM_SESSION", "autosport_session")
    session_path = f"/app/data/{session_name}"

    print(f"Initializing session: {session_path}")
    client = TelegramClient(session_path, api_id, api_hash)
    await client.start()
    print("Authenticated! Session saved.")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())