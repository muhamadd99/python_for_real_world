from __future__ import annotations

import asyncio
import json
import os
import sqlite3
import tempfile
from typing import Callable
from telethon import TelegramClient, events
from telethon.tl.functions.contacts import GetContactsRequest

from .config import Config
from .storage import Storage
from .llm import parse_receipt_text
from .ocr_easy import ocr_image_easyocr
from .pdf_utils import extract_text_from_pdf


async def _run(config: Config, handler: Callable[[str, str], dict], storage: Storage) -> None:
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
        text = event.raw_text.strip() if event.raw_text else ""
        if text.lower() == "/list":
            await send_list(event, config.database_path)
        elif text.lower() == "/deleteall":
            await handle_delete_all(event, storage)
        elif text.lower().startswith("/delete"):
            await handle_delete(event, text, storage)
        elif text.lower().startswith("/uploadtoreceiptdataset"):
            await handle_upload_to_receipt_dataset(event, text, storage, config)

    print("Telegram userbot started. Waiting for receipts...")
    await client.start()
    
    result = await client(GetContactsRequest(hash=0))
    for contact in result.users:
        name = " ".join(filter(None, [contact.first_name, contact.last_name]))
        if name:
            contact_map[contact.id] = name
    contacts_ready.set()

    await client.run_until_disconnected()


def run_userbot(config: Config, handler: Callable[[str, str], dict], storage: Storage) -> None:
    asyncio.run(_run(config, handler, storage))

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
    rows = conn.execute("SELECT id, sender, contact_name, parsed_json FROM receipts").fetchall()
    conn.close()

    if not rows:
        await event.reply("No receipts yet.")
        return

    lines = []
    for row_id, sender, contact_name, parsed in rows:
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
        reasons = data.get("reasons", [])
        line = f"[{row_id}] {payer} — {status} — RM{amount} — {ai_status}"
        if reasons and status in ("INVALID", "FISHY"):
            line += f"\n    └─ {', '.join(reasons)}"
        lines.append(line)

    await event.reply("\n".join(lines))

async def handle_upload_to_receipt_dataset(event, text: str, storage: Storage, config: Config) -> None:
    args = text[len("/uploadtoreceiptdataset"):].strip()

    if event.message.media:
        debug_dir = os.path.join(os.path.dirname(config.database_path), "pdf_converted_pic_debug")
        os.makedirs(debug_dir, exist_ok=True)

        file_path = await event.message.download_media(file=debug_dir)
        if not file_path:
            await event.reply("Failed to download file.")
            return

        ext = file_path.rsplit(".", 1)[-1].lower()
        if ext == "pdf":
            raw_text = extract_text_from_pdf(file_path, ocr_fn=ocr_image_easyocr, force_image=True)
        else:
            raw_text = ocr_image_easyocr(file_path)

        print(f"--- RAW OCR (receipt_dataset) ---\n{raw_text}\n--- END ---")

        receiver_keywords = storage.get_receiver_keywords()
        parsed = parse_receipt_text(raw_text, receiver_keywords)

        if not parsed.get("bank_name") and not parsed.get("reference_id"):
            await event.reply(
                "Could not extract enough fields from receipt.\n"
                "Fallback: use manual format:\n"
                "/uploadtoreceiptdataset bank_name|receiver_name|receiver_keyword|ref_id|transaction_date|transaction_time|currency|currency_keyword"
            )
            return

        storage.save_receipt_dataset(
            bank_name=parsed.get("bank_name") or "",
            receiver_name=parsed.get("receiver_name") or "",
            receiver_keyword=parsed.get("receiver_keyword") or "",
            ref_id=parsed.get("reference_id") or "",
            transaction_date=parsed.get("transaction_date") or "",
            transaction_time=parsed.get("transaction_time") or "",
            currency=parsed.get("currency") or "",
            currency_keyword="",
        )
        await event.reply(
            f"Saved from receipt:\n"
            f"Bank: {parsed.get('bank_name')}\n"
            f"Receiver: {parsed.get('receiver_name')}\n"
            f"Receiver keyword: {parsed.get('receiver_keyword') or 'not detected'}\n"
            f"Ref: {parsed.get('reference_id')}\n"
            f"Date: {parsed.get('transaction_date')}\n"
            f"Time: {parsed.get('transaction_time')}\n"
            f"Currency: {parsed.get('currency')}\n"
            f"Currency keyword: {parsed.get('currency_keyword') or 'not detected'}"
        )
        return

    fields = [f.strip() for f in args.split("|")]
    if len(fields) != 8:
        await event.reply(
            "Usage:\n"
            "1. Attach receipt image/PDF:\n"
            "   /uploadtoreceiptdataset\n\n"
            "2. Manual format (pipe-delimited):\n"
            "   /uploadtoreceiptdataset bank_name|receiver_name|receiver_keyword|ref_id|transaction_date|transaction_time|currency|currency_keyword"
        )
        return

    storage.save_receipt_dataset(
        bank_name=fields[0],
        receiver_name=fields[1],
        receiver_keyword=fields[2],
        ref_id=fields[3],
        transaction_date=fields[4],
        transaction_time=fields[5],
        currency=fields[6],
        currency_keyword=fields[7],
    )
    await event.reply(f"Saved to receipt_dataset: {fields[0]} | {fields[1]} | {fields[6]}")


async def handle_delete(event, text: str, storage: Storage) -> None:
    args = text[len("/delete"):].strip()
    if not args.isdigit():
        await event.reply("Usage: /delete <receipt_id>\nUse /list to see IDs.")
        return
    
    receipt_id = int(args)
    if storage.delete_receipt(receipt_id):
        await event.reply(f"Receipt {receipt_id} deleted.")
    else:
        await event.reply(f"Receipt {receipt_id} not found.")

async def handle_delete_all(event, storage: Storage) -> None:
    count = storage.delete_all_receipts()
    await event.reply(f"Deleted {count} receipts from database.")