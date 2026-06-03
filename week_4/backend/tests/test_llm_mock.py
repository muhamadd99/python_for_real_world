from __future__ import annotations

from src.config import Config
from src.llm import parse_receipt_text


def test_parse_receipt_text_valid() -> None:
    text = "Maybank Reference ID: ABC12345 RM 50.00 02/06/2026 10:30"
    config = Config(
        telegram_api_id=None,
        telegram_api_hash=None,
        telegram_session=None,
        llm_provider="mock",
        llm_api_key=None,
        ocr_engine="tesseract",
        database_path=":memory:",
    )

    parsed = parse_receipt_text(text, config)

    assert parsed["bank_name"] == "Maybank"
    assert parsed["amount"] == "50.00"
    assert parsed["reference_id"] == "ABC12345"
    assert parsed["status"] == "VALID"


def test_parse_receipt_text_missing_fields() -> None:
    text = "Transfer completed"
    config = Config(
        telegram_api_id=None,
        telegram_api_hash=None,
        telegram_session=None,
        llm_provider="mock",
        llm_api_key=None,
        ocr_engine="tesseract",
        database_path=":memory:",
    )

    parsed = parse_receipt_text(text, config)

    assert parsed["status"] == "INVALID"
    assert "missing_required_fields" in parsed["reasons"]
