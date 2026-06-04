from __future__ import annotations

import json
import re
import urllib.request

from .config import Config


SYSTEM_PROMPT = (
    "You are AutoSport-Pay, an AI payment verification assistant. "
    "Parse OCR text from bank receipts and return strict JSON only."
)


def parse_receipt_text(text: str, config: Config) -> dict:
    provider = config.llm_provider.lower()
    if provider == "openai":
        return _parse_with_openai(text, config)
    if provider in {"gemini", "googlegenai", "google"}:
        return _parse_with_gemini(text, config)
    return _parse_with_mock(text)


def _parse_with_mock(text: str) -> dict:
    bank_name = _find_bank_name(text)
    payer_name = _find_payer_name(text)
    amount = _find_amount(text)
    reference_id = _find_reference_id(text)
    date = _find_date(text)
    time = _find_time(text)

    reasons = []
    status = "VALID"
    missing = []
    if not amount:
        missing.append("amount")
    if not reference_id:
        missing.append("reference_id")
        
    date_missing = not date

    if missing:
        status = "INVALID"
        reasons.append(f"missing_required_fields: {', '.join(missing)}")
    elif date_missing:
        status = "OKLAH"
        reasons.append("missing_optional_fields: transaction_date")

    return {
        "bank_name": bank_name,
        "payer_name": payer_name,
        "amount": amount,
        "currency": _find_currency(text),
        "reference_id": reference_id,
        "transaction_date": date,
        "transaction_time": time,
        "status": status,
        "reasons": reasons,
    }


def _parse_with_openai(text: str, config: Config) -> dict:
    if not config.llm_api_key:
        raise RuntimeError("LLM_API_KEY is required for OpenAI provider")

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        "temperature": 0,
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=data,
        headers={
            "Authorization": f"Bearer {config.llm_api_key}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        body = json.loads(response.read().decode("utf-8"))

    content = body["choices"][0]["message"]["content"]
    return json.loads(content)


def _parse_with_gemini(text: str, config: Config) -> dict:
    if not config.llm_api_key:
        raise RuntimeError("LLM_API_KEY is required for Gemini provider")

    payload = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [
            {
                "role": "user",
                "parts": [{"text": text}],
            }
        ],
        "generationConfig": {"temperature": 0},
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-1.5-flash:generateContent?key="
        f"{config.llm_api_key}",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        body = json.loads(response.read().decode("utf-8"))

    candidates = body.get("candidates", [])
    if not candidates:
        raise RuntimeError("Gemini response missing candidates")

    parts = candidates[0].get("content", {}).get("parts", [])
    if not parts:
        raise RuntimeError("Gemini response missing content parts")

    content = parts[0].get("text", "")
    return json.loads(content)


def _find_bank_name(text: str) -> str | None:
    candidates = ["maybank", "cimb", "duitnow", "public bank", "rhb", "hsbc"]
    lower = text.lower()
    for name in candidates:
        if name in lower:
            return name.title()
    return None


def _find_amount(text: str) -> str | None:
    match = re.search(r"(RM|MYR)\s?([0-9]+(?:\.[0-9]{2})?)", text, re.IGNORECASE)
    if match:
        return match.group(2)
    return None


def _find_currency(text: str) -> str | None:
    if re.search(r"\bRM\b|\bMYR\b", text, re.IGNORECASE):
        return "MYR"
    return None


def _find_reference_id(text: str) -> str | None:
    patterns = [
        r"reference\s*(id|no\.?)\s*[:\s]*\s*([A-Za-z0-9\-]{6,})",
        r"ref\s*[:\s]+([A-Za-z0-9\-]{6,})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(match.lastindex)
    return None


def _find_date(text: str) -> str | None:
    match = re.search(r"(\d{2}[/-]\d{2}[/-]\d{4})", text)
    if match:
        return match.group(1)
    match = re.search(r"\b(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[,\s]+(\d{4})\b", text, re.IGNORECASE) #maybank date format
    if match:
        return f"{match.group(1)} {match.group(2).capitalize()} {match.group(3)}"
    return None


def _find_time(text: str) -> str | None:
    match = re.search(r"(\d{2}:\d{2}(?::\d{2})?)", text)
    return match.group(1) if match else None

def _find_payer_name(text: str) -> str | None:
    match = re.search(r"beneficiary\s*name\s*\n\s*(.+)", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None
