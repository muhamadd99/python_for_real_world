from __future__ import annotations

import os

from dotenv import load_dotenv
from .config import Config
from .processor import process_receipt
from .storage import Storage
from .telegram_bot import run_userbot


def main() -> None:
    load_dotenv()
    
	# Debug: Check if env vars are loaded
    print(f"TELEGRAM_API_ID: {os.getenv('TELEGRAM_API_ID')}")
    print(f"TELEGRAM_API_HASH: {os.getenv('TELEGRAM_API_HASH')}")
    print(f"TELEGRAM_SESSION: {os.getenv('TELEGRAM_SESSION')}")
    config = Config.from_env()
    print(f"Config: {config}")  # This will show if config loaded correctl

    config = Config.from_env()
    storage = Storage(config.database_path)
    storage.init_schema()

    def handler(file_path: str, sender: str) -> dict:
        return process_receipt(file_path, sender, storage, config)

    run_userbot(config, handler)


if __name__ == "__main__":
    main()
