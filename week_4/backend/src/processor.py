from __future__ import annotations

import os

from .config import Config
from .llm import parse_receipt_text
from .ocr import ocr_image
from .pdf_utils import extract_text_from_pdf
from .storage import Storage
from .validator import validate_receipt


def process_receipt(file_path: str, sender: str, storage: Storage, config: Config) -> dict:
    ext = os.path.splitext(file_path)[1].lower()
    if ext in {".pdf"}:
        raw_text = extract_text_from_pdf(file_path)
    else:
        raw_text = ocr_image(file_path)

    parsed = parse_receipt_text(raw_text, config)
    parsed = validate_receipt(parsed, storage)
    storage.save_receipt(sender, file_path, raw_text, parsed)
    return parsed
