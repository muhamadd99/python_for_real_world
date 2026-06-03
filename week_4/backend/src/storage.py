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
                CREATE TABLE IF NOT EXISTS bank_blueprints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bank_name TEXT,
                    rules_json TEXT
                )
                """
            )

    def save_receipt(self, sender: str, file_path: str, raw_text: str, parsed: dict) -> None:
        parsed_json = json.dumps(parsed, ensure_ascii=True)
        reference_id = parsed.get("reference_id") if isinstance(parsed, dict) else None
        status = parsed.get("status") if isinstance(parsed, dict) else None
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO receipts (sender, file_path, raw_text, parsed_json, status, reference_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (sender, file_path, raw_text, parsed_json, status, reference_id),
            )

    def has_reference_id(self, reference_id: str) -> bool:
        with self.connect() as conn:
            cursor = conn.execute(
                "SELECT 1 FROM receipts WHERE reference_id = ? LIMIT 1", (reference_id,)
            )
            return cursor.fetchone() is not None
