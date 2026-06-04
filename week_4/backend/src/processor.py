from __future__ import annotations

import os

from .config import Config
from .llm import parse_receipt_text
from .ocr import ocr_image
from .pdf_utils import extract_text_from_pdf
from .storage import Storage
from .validator import validate_receipt


def process_receipt(file_path: str, sender: str, storage: Storage, config: Config, contact_name: str = None) -> dict:
    ext = os.path.splitext(file_path)[1].lower()
    if ext in {".pdf"}:
        raw_text = extract_text_from_pdf(file_path)
    else:
        raw_text = ocr_image(file_path)

    import sys #debug
    print(f"--- RAW OCR ---\n{raw_text}\n--- END ---", flush=True, file=sys.stderr) #debug
    parsed = parse_receipt_text(raw_text, config)
    parsed = validate_receipt(parsed, storage)
    if contact_name:
        parsed["contact_name"] = contact_name
    storage.save_receipt(sender, file_path, raw_text, parsed)
    print(f"SAVE DONE: sender={sender} ref={parsed.get('reference_id')}") #debug
    return parsed
