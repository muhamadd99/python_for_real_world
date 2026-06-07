from __future__ import annotations

from .storage import Storage


def validate_receipt(parsed: dict, storage: Storage) -> dict:
    reasons = list(parsed.get("reasons", []))
    status = parsed.get("status", "INVALID")

    reference_id = parsed.get("reference_id")
    amount = parsed.get("amount")
    date = parsed.get("transaction_date")

    if not reference_id or not amount or not date:
        status = "INVALID"
        missing = []
        if not reference_id:
            missing.append("reference_id")
        if not amount:
            missing.append("amount")
        
        date_missing = not date
        
        if missing:
            status = "INVALID"
            reason = f"missing: {', '.join(missing)}"
            if reason not in reasons:
                reasons.append(reason)
        elif date_missing and status != "FISHY":
            status = "OKLAH"
            if "missing: transaction_date" not in reasons:
                reasons.append("missing: transaction_date")

    if reference_id and storage.has_reference_id(reference_id):
        status = "FISHY"
        reasons.append("duplicate_reference_id")

    parsed["status"] = status
    parsed["reasons"] = reasons
    return parsed
