from __future__ import annotations

import asyncio
import os
import tempfile
from typing import Callable

from .config import Config


async def _run(config: Config, handler: Callable[[str, str], dict]) -> None:
    try:
        from telethon import TelegramClient, events
    except ImportError as exc:
        raise RuntimeError("telethon is required for Telegram userbot") from exc

    if not config.telegram_api_id or not config.telegram_api_hash or not config.telegram_session:
        raise RuntimeError("Telegram config missing. Set TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_SESSION")

    client = TelegramClient(
        f"/app/data/{config.telegram_session}", config.telegram_api_id, config.telegram_api_hash
    )

    @client.on(events.NewMessage(incoming=True))
    async def on_message(event) -> None:
        if not event.message.media:
            return

        sender = str(event.sender_id)
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = await event.message.download_media(file=tmp_dir)
            if not file_path:
                return

            result = handler(file_path, sender)
            status = result.get("status")
            reference_id = result.get("reference_id")
            print(f"receipt processed: sender={sender} status={status} ref={reference_id}")

    print("Telegram userbot started. Waiting for receipts...")
    await client.start()
    await client.run_until_disconnected()


def run_userbot(config: Config, handler: Callable[[str, str], dict]) -> None:
    asyncio.run(_run(config, handler))