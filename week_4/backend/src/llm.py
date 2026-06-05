"""
llm.py  — AutoSport-Pay receipt parser
Replaces the original llm.py that had two critical bugs:
  1. _find_bank_name() matched "duitnow" and returned it as the bank name.
  2. _parse_with_mock() captured payer_name instead of receiver_name,
     so receiver_name was always None in the output dict.
"""
from __future__ import annotations

import json
import re
import urllib.request
from typing import Optional

from .config import Config


SYSTEM_PROMPT = (
    "You are AutoSport-Pay, an AI payment verification assistant. "
    "Parse OCR text from bank receipts and return strict JSON only."
)

# ---------------------------------------------------------------------------
# Bank-specific receiver/recipient label vocabulary (extensible)
# ---------------------------------------------------------------------------
RECEIVER_LABELS_BY_BANK: dict[str, list[str]] = {
    "maybank":    ["Beneficiary Name", "Recipient Name", "Recipient", "To", "Transfer To"],
    "rhb":        ["To", "Recipient", "Beneficiary", "Receiving Party"],
    "bsn":        ["Transfer To", "Recipient", "Beneficiary", "Account Name"],
    "bank_islam": ["Recipient Name", "Penerima", "To", "Nama Penerima"],
    "cimb":       ["Recipient", "Beneficiary", "To", "Payee"],
    "public_bank":["Beneficiary", "Penerima", "Recipient", "Beneficiary Name"],
    "hong_leong": ["To", "Beneficiary Name", "Recipient", "Payee Name"],
    "ambank":     ["To", "Recipient Name", "Beneficiary Name", "Transfer To"],
    "generic": [
        "receiver name", "receiver",
        "recipient name", "recipient",
        "beneficiary name", "beneficiary",
        "payee name", "payee",
        "transfer to",
        "penerima", "nama penerima",
        "to",          # keep "to" last — it's very short and can false-match
    ],
}

# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def parse_receipt_text(text: str, config: Config) -> dict:
    """
    Orchestrates extraction:
      1. OpenAI (if configured)
      2. Gemini  (if configured)
      3. Local regex fallback (_parse_with_enhanced_mock)
    """
    provider = (config.llm_provider or "mock").lower()

    if provider == "openai":
        return _parse_with_openai(text, config)
    if provider in {"gemini", "googlegenai", "google"}:
        return _parse_with_gemini(text, config)

    return _parse_with_enhanced_mock(text)


# ---------------------------------------------------------------------------
# Local regex fallback — the path most users hit in development
# ---------------------------------------------------------------------------

def _parse_with_enhanced_mock(text: str) -> dict:
    """
    Rule-based parser used when no LLM provider is configured.

    BUG FIXED (payer_name / receiver_name swap):
      The original code built the result dict with key "payer_name" but the
      rest of the system expected "receiver_name".  The value was also sourced
      from _find_bank_name (wrong function call).  Both are corrected here.
    """
    bank_name    = _find_bank_name(text)
    bank_type    = _map_bank_type(bank_name)

    # ---- FIXED: was assigned to "payer_name" with wrong function call ----
    receiver_name = _find_receiver_name(text, bank_type)

    amount        = _find_amount(text)
    reference_id  = _find_reference_id(text)
    date          = _find_date(text)
    time          = _find_time(text)
    currency      = _find_currency(text)

    reasons: list[str] = []
    status = "VALID"

    if not amount or not reference_id or not date:
        status = "INVALID"
        reasons.append("missing_required_fields")

    if not receiver_name:
        reasons.append("missing_receiver_name")

    return {
        "bank_name":        bank_name,
        "receiver_name":    receiver_name,   # ← correct key, correct value
        "amount":           amount,
        "currency":         currency,
        "reference_id":     reference_id,
        "transaction_date": date,
        "transaction_time": time,
        "status":           status,
        "reasons":          reasons,
    }


# ---------------------------------------------------------------------------
# LLM back-ends
# ---------------------------------------------------------------------------

def _parse_with_openai(text: str, config: Config) -> dict:
    if not config.llm_api_key:
        raise RuntimeError("LLM_API_KEY is required for OpenAI provider")

    prompt  = _build_extraction_prompt(text)
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": prompt},
        ],
        "temperature": 0,
    }

    data    = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=data,
        headers={
            "Authorization": f"Bearer {config.llm_api_key}",
            "Content-Type":  "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = json.loads(response.read().decode("utf-8"))
        content = body["choices"][0]["message"]["content"]
        return json.loads(content)
    except Exception:
        return _parse_with_enhanced_mock(text)


def _parse_with_gemini(text: str, config: Config) -> dict:
    if not config.llm_api_key:
        raise RuntimeError("LLM_API_KEY is required for Gemini provider")

    prompt  = _build_extraction_prompt(text)
    payload = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0},
    }

    data    = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-1.5-flash:generateContent?key={config.llm_api_key}",
        data=data,
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = json.loads(response.read().decode("utf-8"))
        candidates = body.get("candidates", [])
        if not candidates:
            return _parse_with_enhanced_mock(text)
        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            return _parse_with_enhanced_mock(text)
        content = parts[0].get("text", "")
        content = content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)
    except Exception:
        return _parse_with_enhanced_mock(text)


# ---------------------------------------------------------------------------
# Prompt builder (shared by OpenAI + Gemini)
# ---------------------------------------------------------------------------

def _build_extraction_prompt(text: str) -> str:
    return f"""
Parse this Malaysian bank transfer receipt and extract the listed fields.

IMPORTANT — RECIPIENT IDENTIFICATION:
Different Malaysian banks use different labels for the fund receiver.  Do NOT
rely on a single fixed label.  Scan the full receipt and match any of these:

  Maybank    : "Beneficiary Name", "Recipient Name", "To"
  RHB        : "To", "Recipient", "Beneficiary"
  BSN        : "Transfer To", "Recipient"
  CIMB       : "Recipient", "Beneficiary", "To"
  Public Bank / Bank Islam : "Beneficiary", "Penerima", "Recipient Name"
  Hong Leong / AmBank / Others : "To", "Payee", "Beneficiary Name"

The field you capture must be the RECEIVER (money destination), not the sender.
Map the result to the key "receiver_name".

Receipt text:
-----------
{text}
-----------

Return ONLY a valid minified JSON object with these exact keys:
{{"bank_name": "string|null", "receiver_name": "string|null", "amount": "string|null", \
"currency": "MYR", "reference_id": "string|null", "transaction_date": "string|null", \
"transaction_time": "string|null"}}
"""


# ---------------------------------------------------------------------------
# Field-extraction helpers
# ---------------------------------------------------------------------------

def _find_receiver_name(text: str, bank_type: str = "generic") -> Optional[str]:
    """
    Case-insensitive scan for receiver/recipient name.
    Tries bank-specific labels first, then the generic list.
    Each label is matched by: LABEL [optional :=- ] VALUE (up to end-of-line).
    """
    labels: list[str] = []
    labels += RECEIVER_LABELS_BY_BANK.get(bank_type, [])
    # Append generics only if not already included
    for g in RECEIVER_LABELS_BY_BANK["generic"]:
        if g not in [l.lower() for l in labels]:
            labels.append(g)

    for label in labels:
        pattern = (
            rf"(?:^|\n)"                              # start of line
            rf"\s*{re.escape(label)}\s*"              # the label (case-insensitive)
            rf"[:=\-]?\s*"                            # optional separator
            rf"([A-Za-z][A-Za-z0-9\s\.&,'\-\(\)]+?)"# name — must start with a letter
            rf"\s*(?:\n|$)"                           # end of line
        )
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            name = match.group(1).strip()
            # Reject noise: currency symbols, very short tokens, known non-name values
            if (
                len(name) > 2
                and not re.match(r'^(RM|MYR|USD)', name, re.IGNORECASE)
                and not name.lower().startswith("amount")
            ):
                return name

    return None


def _find_bank_name(text: str) -> Optional[str]:
    """
    BUG FIXED: the original list included "duitnow" which caused DuitNow
    QR receipts to be misidentified as a bank called "Duitnow".
    DuitNow is a payment rail, not a bank — removed from this list.
    """
    candidates = [
        ("maybank",     "Maybank"),
        ("cimb",        "CIMB"),
        ("public bank", "Public Bank"),
        ("rhb",         "RHB"),
        ("hsbc",        "HSBC"),
        ("bsn",         "BSN"),
        ("bank islam",  "Bank Islam"),
        ("ambank",      "AmBank"),
        ("hong leong",  "Hong Leong Bank"),
        ("hlb",         "Hong Leong Bank"),
    ]
    lower = text.lower()
    for keyword, display in candidates:
        if keyword in lower:
            return display
    return None


def _map_bank_type(bank_name: Optional[str]) -> str:
    if not bank_name:
        return "generic"
    b = bank_name.lower()
    if "maybank" in b:
        return "maybank"
    if "rhb" in b:
        return "rhb"
    if "bsn" in b or "simpanan" in b:
        return "bsn"
    if "bank islam" in b:
        return "bank_islam"
    if "cimb" in b:
        return "cimb"
    if "public" in b:
        return "public_bank"
    if "hong leong" in b or "hlb" in b:
        return "hong_leong"
    if "ambank" in b:
        return "ambank"
    return "generic"


def _find_amount(text: str) -> Optional[str]:
    match = re.search(r"(RM|MYR)\s?([0-9]+(?:\.[0-9]{2})?)", text, re.IGNORECASE)
    return match.group(2) if match else None


def _find_currency(text: str) -> Optional[str]:
    return "MYR" if re.search(r"\bRM\b|\bMYR\b", text, re.IGNORECASE) else None


def _find_reference_id(text: str) -> Optional[str]:
    patterns = [
        r"reference\s*(?:id|no)?[\s:=\-]+([A-Za-z0-9\-]{6,})",
        r"\bref(?:no|\.no)?[\s:=\-]+([A-Za-z0-9\-]{6,})",
        r"transaction\s*no[\s:=\-]+([A-Za-z0-9\-]{6,})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(match.lastindex)
    return None


def _find_date(text: str) -> Optional[str]:
    match = re.search(r"(\d{2}[/-]\d{2}[/-]\d{4})|(\d{4}-\d{2}-\d{2})", text)
    return match.group(0) if match else None


def _find_time(text: str) -> Optional[str]:
    match = re.search(r"(\d{2}:\d{2}(?::\d{2})?)", text)
    return match.group(1) if match else None