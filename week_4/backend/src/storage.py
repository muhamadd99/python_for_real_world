from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass


@dataclass
class Storage:
    db_path: str

    def connect(self) -> sqlite3.Connection:
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        return sqlite3.connect(self.db_path)

    def init_schema(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS receipts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender TEXT,
                    contact_name TEXT,
                    file_path TEXT,
                    raw_text TEXT,
                    parsed_json TEXT,
                    status TEXT,
                    reference_id TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS receipt_dataset (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bank_name TEXT,
                    receiver_name TEXT,
                    receiver_keyword TEXT,
                    ref_id TEXT,
                    ref_keyword TEXT,
                    transaction_date TEXT,
                    transaction_time TEXT,
                    currency TEXT,
                    currency_keyword TEXT
                )
                """
            )

    def save_receipt(self, sender: str, file_path: str, raw_text: str, parsed: dict) -> None:
        parsed_clean = {k: v for k, v in parsed.items() if k not in ("receiver_keyword", "ref_keyword", "currency_keyword")}
        parsed_json = json.dumps(parsed_clean, ensure_ascii=True)
        reference_id = parsed.get("reference_id") if isinstance(parsed, dict) else None
        status = parsed.get("status") if isinstance(parsed, dict) else None
        contact_name = parsed.get("contact_name")
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO receipts (sender, contact_name, file_path, raw_text, parsed_json, status, reference_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (sender, contact_name, file_path, raw_text, parsed_json, status, reference_id),
            )

    def has_reference_id(self, reference_id: str) -> bool:
        with self.connect() as conn:
            cursor = conn.execute(
                "SELECT 1 FROM receipts WHERE reference_id = ? LIMIT 1", (reference_id,)
            )
            return cursor.fetchone() is not None

    def save_receipt_dataset(self, bank_name: str, receiver_name: str, receiver_keyword: str,
                             ref_id: str, ref_keyword: str, transaction_date: str, transaction_time: str,
                             currency: str, currency_keyword: str) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO receipt_dataset
                    (bank_name, receiver_name, receiver_keyword, ref_id, ref_keyword,
                     transaction_date, transaction_time, currency, currency_keyword)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (bank_name, receiver_name, receiver_keyword, ref_id, ref_keyword,
                 transaction_date, transaction_time, currency, currency_keyword),
            )

    def get_currency_keywords(self, bank_name: str | None = None) -> list[str]:
        with self.connect() as conn:
            if bank_name:
                cursor = conn.execute(
                    "SELECT DISTINCT currency_keyword FROM receipt_dataset WHERE bank_name = ?",
                    (bank_name,),
                )
            else:
                cursor = conn.execute(
                    "SELECT DISTINCT currency_keyword FROM receipt_dataset"
                )
            return [row[0] for row in cursor.fetchall() if row[0]]

    def get_receiver_keywords(self, bank_name: str | None = None) -> list[str]:
        with self.connect() as conn:
            if bank_name:
                cursor = conn.execute(
                    "SELECT DISTINCT receiver_keyword FROM receipt_dataset WHERE bank_name = ?",
                    (bank_name,),
                )
            else:
                cursor = conn.execute(
                    "SELECT DISTINCT receiver_keyword FROM receipt_dataset"
                )
            return [row[0] for row in cursor.fetchall() if row[0]]

    def get_ref_keywords(self, bank_name: str | None = None) -> list[str]:
        with self.connect() as conn:
            if bank_name:
                cursor = conn.execute(
                    "SELECT DISTINCT ref_keyword FROM receipt_dataset WHERE bank_name = ?",
                    (bank_name,),
                )
            else:
                cursor = conn.execute(
                    "SELECT DISTINCT ref_keyword FROM receipt_dataset"
                )
            return [row[0] for row in cursor.fetchall() if row[0]]
        
    def delete_receipt(self, receipt_id: int) -> bool:
        with self.connect() as conn:
            cursor = conn.execute("DELETE FROM receipts WHERE id = ?", (receipt_id,))
            if cursor.rowcount > 0:
                conn.execute("""
                    UPDATE receipts SET id = (
                        SELECT COUNT(*) FROM receipts r2 
                        WHERE r2.id <= receipts.id
                    )
                """)
                conn.execute("DELETE FROM sqlite_sequence WHERE name = 'receipts'")
                return True
            return False

    def delete_all_receipts(self) -> int:
        with self.connect() as conn:
            cursor = conn.execute("DELETE FROM receipts")
            conn.execute("DELETE FROM sqlite_sequence WHERE name = 'receipts'")
            return cursor.rowcount
        
    def get_all_receipts(self) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT id, sender, contact_name, parsed_json, status, reference_id FROM receipts ORDER BY id DESC"
            ).fetchall()
        results = []
        for row_id, sender, contact_name, parsed_json, status, reference_id in rows:
            parsed = json.loads(parsed_json) if parsed_json else {}
            results.append({
                "id": row_id,
                "sender": sender,
                "contact_name": contact_name,
                "status": status,
                "reference_id": reference_id,
                "reasons": parsed.get("reasons", []),
                "amount": parsed.get("amount"),
                "bank_name": parsed.get("bank_name"),
                "receiver_name": parsed.get("receiver_name"),
                "ref_keyword": parsed.get("ref_keyword"),
                "transaction_date": parsed.get("transaction_date"),
            })
        return results
