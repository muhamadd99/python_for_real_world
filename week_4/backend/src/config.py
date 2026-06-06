from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Config:
    telegram_api_id: int | None
    telegram_api_hash: str | None
    telegram_session: str | None
    llm_provider: str
    llm_api_key: str | None
    database_path: str

    @staticmethod
    def from_env() -> "Config":
        api_id_raw = os.getenv("TELEGRAM_API_ID")
        api_id = int(api_id_raw) if api_id_raw and api_id_raw.isdigit() else None

        return Config(
            telegram_api_id=api_id,
            telegram_api_hash=os.getenv("TELEGRAM_API_HASH"),
            telegram_session=os.getenv("TELEGRAM_SESSION"),
            llm_provider=os.getenv("LLM_PROVIDER", "mock"),
            llm_api_key=os.getenv("LLM_API_KEY"),
            database_path=os.getenv("DATABASE_PATH", "./data/autosport_pay.db"),
        )
