from __future__ import annotations

from src.storage import Storage
from src.validator import validate_receipt


def test_validator_detects_duplicate_reference(tmp_path) -> None:
    db_path = tmp_path / "autosport.db"
    storage = Storage(str(db_path))
    storage.init_schema()

    parsed = {
        "reference_id": "REF123",
        "amount": "20.00",
        "transaction_date": "02/06/2026",
        "status": "VALID",
        "reasons": [],
    }

    storage.save_receipt("sender", "file.png", "raw", parsed)

    second = validate_receipt(parsed.copy(), storage)
    assert second["status"] == "FISHY"
    assert "duplicate_reference_id" in second["reasons"]
