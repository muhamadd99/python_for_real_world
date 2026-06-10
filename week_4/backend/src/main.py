from __future__ import annotations

import os

from dotenv import load_dotenv
from .config import Config
from .processor import process_receipt
from .storage import Storage
from .telegram_bot import run_userbot


def main() -> None:
    load_dotenv()

    config = Config.from_env()
    storage = Storage(config.database_path)
    storage.init_schema()

    def handler(file_path: str, sender: str, contact_name: str = None) -> dict:
        return process_receipt(file_path, sender, storage, config, contact_name)

    run_userbot(config, handler, storage)


if __name__ == "__main__":
    main()
