from __future__ import annotations

import os

from .config import Config
from .llm import parse_receipt_text, confirm_amount_with_ai
from .ocr_easy import ocr_image_easyocr as ocr_image
from .pdf_utils import extract_text_from_pdf
from .storage import Storage
from .validator import validate_receipt


def process_receipt(file_path: str, sender: str, storage: Storage, config: Config, contact_name: str = None) -> dict:
    ext = os.path.splitext(file_path)[1].lower()
    if ext in {".pdf"}:
        raw_text = extract_text_from_pdf(file_path, force_image=True)
    else:
        raw_text = ocr_image(file_path)

    import sys #debug
    print(f"--- RAW OCR ---\n{raw_text}\n--- END ---", flush=True, file=sys.stderr) #debug
    receiver_keywords = storage.get_receiver_keywords()
    parsed = parse_receipt_text(raw_text, receiver_keywords)
    
    print(f"[DEBUG] after parse_receipt_text: amount={parsed.get('amount')} ref={parsed.get('reference_id')} date={parsed.get('transaction_date')}", flush=True, file=sys.stderr)

    parsed = confirm_amount_with_ai(parsed, raw_text, config)
    
    print(f"[DEBUG] after confirm_amount_with_ai: status={parsed.get('status')} reasons={parsed.get('reasons')} amount={parsed.get('amount')} ref={parsed.get('reference_id')} date={parsed.get('transaction_date')}", flush=True, file=sys.stderr)

    parsed = validate_receipt(parsed, storage)

    print(f"[DEBUG] after validate_receipt: status={parsed.get('status')} reasons={parsed.get('reasons')}", flush=True, file=sys.stderr)

    if contact_name:
        parsed["contact_name"] = contact_name
    storage.save_receipt(sender, file_path, raw_text, parsed)
    print(f"SAVE DONE: sender={sender} ref={parsed.get('reference_id')}") #debug
    return parsed
