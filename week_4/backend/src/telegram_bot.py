from __future__ import annotations

import asyncio
import json
import sqlite3
import tempfile
from typing import Callable
from telethon import TelegramClient, events
from telethon.tl.functions.contacts import GetContactsRequest

from .config import Config


async def _run(config: Config, handler: Callable[[str, str], dict]) -> None:
    if not config.telegram_api_id or not config.telegram_api_hash or not config.telegram_session:
        raise RuntimeError("Telegram config missing. Set TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_SESSION")

    client = TelegramClient(
        f"/app/data/{config.telegram_session}", config.telegram_api_id, config.telegram_api_hash
    )

    contact_map = {}
    contacts_ready = asyncio.Event()

    @client.on(events.NewMessage(incoming=True))
    async def on_incoming(event) -> None:
        print(f"DEBUG: chat_id={event.chat_id} text={event.raw_text}") #debug
        if not event.message.media:
            return
        await contacts_ready.wait()
        await process_receipt(event, handler, contact_map, client)

    @client.on(events.NewMessage(outgoing=True))
    async def on_outgoing(event) -> None:
        if event.raw_text and event.raw_text.strip().lower() == "/list":
            await send_list(event, config.database_path)

    print("Telegram userbot started. Waiting for receipts...")
    await client.start()
    
    result = await client(GetContactsRequest(hash=0))
    for contact in result.users:
        name = " ".join(filter(None, [contact.first_name, contact.last_name]))
        if name:
            contact_map[contact.id] = name
    contacts_ready.set()

    await client.run_until_disconnected()


def run_userbot(config: Config, handler: Callable[[str, str], dict]) -> None:
    asyncio.run(_run(config, handler))

async def process_receipt(event, handler: Callable[[str, str], dict], contact_map: dict,client) -> None:
    sender_id = str(event.sender_id)
    contact_name = await get_contact_name(sender_id, contact_map, client)

    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = await event.message.download_media(file=tmp_dir)
        if not file_path:
            return

        result = handler(file_path, sender_id, contact_name)
        status = result.get("status")
        reference_id = result.get("reference_id")
        print(f"receipt processed: sender={contact_name} status={status} ref={reference_id}")
        print(f"  DEBUG reasons={result.get('reasons')} amount={result.get('amount')} date={result.get('transaction_date')}")

async def get_contact_name(sender_id: str, contact_map: dict, client) -> str:
    uid = int(sender_id)
    if uid in contact_map:
        return contact_map[uid]
    try:
        entity = await client.get_entity(uid)
        return " ".join(filter(None, [entity.first_name, entity.last_name])) or sender_id
    except Exception:
        return sender_id

async def send_list(event, db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT sender, contact_name, parsed_json FROM receipts").fetchall()
    conn.close()

    if not rows:
        await event.reply("No receipts yet.")
        return

    lines = []
    for sender, contact_name, parsed in rows:
        data = json.loads(parsed)
        payer = contact_name or sender
        status = data.get("status")
        amount = data.get("amount")
        amount_confirmed = data.get("amount_confirmed")
        if amount_confirmed is True:
            ai_status = "AI CONFIRMED"
        elif amount_confirmed is False:
            ai_status = f"AI OVERWRITE{{{data.get('amount_regex')}}}"
        else:
            ai_status = "NO AI CHECK"
        lines.append(f"{payer} — {status} — RM{amount} — {ai_status}")

    await event.reply("\n".join(lines))


