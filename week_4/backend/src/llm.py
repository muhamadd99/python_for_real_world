from __future__ import annotations

import json
import re
import urllib.request
from google import genai
from google.genai.errors import APIError

from .config import Config


SYSTEM_PROMPT = (
    "You are AutoSport-Pay, an AI payment verification assistant. "
    "Parse OCR text from bank receipts and return strict JSON only."
)

def parse_receipt_text(text: str, receiver_keywords: list[str] | None = None) -> dict:
    bank_name = _find_bank_name(text)
    receiver_name = _find_receiver_name(text, receiver_keywords)
    receiver_keyword, receiver_from_keyword = _find_receiver_keyword(text)
    if not receiver_name:
        receiver_name = receiver_from_keyword
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
        reasons.append(f"missings: {', '.join(missing)}")
    elif date_missing:
        status = "OKLAH"
        reasons.append("missing: transaction_date")

    return {
        "bank_name": bank_name,
        "receiver_name": receiver_name,
        "receiver_keyword": receiver_keyword,
        "amount": amount,
        "currency": _find_currency(text),
        "reference_id": reference_id,
        "transaction_date": date,
        "transaction_time": time,
        "status": status,
        "reasons": reasons,
    }

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
    match = re.search(r"(\d{1,2}:\d{2}(?::\d{2})?)\s*(am|pm)?", text, re.IGNORECASE)
    if match:
        time_str = match.group(1)
        suffix = (match.group(2) or "").lower()
        if len(time_str) == 4:
            time_str = "0" + time_str
        if suffix:
            time_str += " " + suffix.upper()
        return time_str
    return None

def _find_receiver_name(text: str, receiver_keywords: list[str] | None = None):
    if receiver_keywords:
        for keyword in receiver_keywords:
            pattern = re.escape(keyword) + r"\s*[:\s]\s*(.+)"
            match = re.search(pattern, text, re.IGNORECASE)
            # DEBUG START
            import sys
            escaped = re.escape(keyword)
            print(f"[DEBUG] keyword='{keyword}'  escaped='{escaped}'  pattern='{pattern}'  match={'YES -> ' + repr(match.group(1).strip()) if match else 'NO'}", file=sys.stderr, flush=True)
            # DEBUG END
            if match:
                return match.group(1).strip()

    return None

CURRENCY_KEYWORDS = {"RM", "MYR", "RM1", "RM2", "RM3", "RM4", "RM5", "RM6", "RM7", "RM8", "RM9"}

RECEIVER_LABELS = {"to", "beneficiary", "recipient", "payee", "receiver", "transfer", "name"}

def _find_receiver_keyword(text: str) -> tuple[str, str] | tuple[None, None]:
    matches = re.findall(r"(\w+[.:]?)\s*\n\s*([A-Z][A-Z\s]{3,})", text)
    for keyword, name in reversed(matches):
        if keyword.lower().rstrip(":.") not in RECEIVER_LABELS:
            continue
        name_clean = re.sub(r"\s+", "", name)
        if len(name_clean) >= 5 and name_clean.upper() not in CURRENCY_KEYWORDS:
            return keyword, name.strip()
    return None, None

def confirm_amount_with_ai(parsed: dict, raw_text: str, config: Config) -> dict:
    """Use LLM to confirm the regex-extracted amount."""
    if config.llm_provider.lower() == "mock":
        parsed["amount_confirmed"] = None
        return parsed

    regex_amount = parsed.get("amount")
    if not regex_amount:
        return parsed  # nothing to confirm

    result = _ask_llm_for_amount(regex_amount, raw_text, config)

    if result is not None and result[0] == "yes":
        parsed["amount_confirmed"] = True
        parsed["amount_llm_value"] = regex_amount
    else:
        parsed["amount_confirmed"] = False
        parsed["status"] = "FISHY"
        parsed["reasons"] = list(parsed.get("reasons", []))

        if result is None:
            parsed["amount_llm_value"] = None
            parsed["reasons"].append("amount_confirmation_failed: LLM returned no response")
        else:
            parsed["amount_llm_value"] = result[1] if len(result) > 1 else None
            parsed["amount_regex"] = regex_amount
            parsed["amount"] = result[1] if len(result) > 1 else parsed["amount"]
            parsed["reasons"].append(
                f"amount_mismatch: regex={regex_amount}, llm={parsed['amount_llm_value']}"
            )

    return parsed

def _ask_llm_for_amount(regex_amount: str, raw_text: str, config: Config) -> list | None:
    """Ask LLM to confirm the extracted amount. Returns a list like ['yes'] or ['no', '42.50']."""
    prompt = (
        "A receipt was parsed and the transaction amount was extracted as: "
        f"{regex_amount}.\n\n"
        "Review the receipt text below and confirm if this amount is correct.\n\n"
        "Respond with a JSON list:\n"
        '["yes"] if the amount is correct.\n'
        '["no", "<correct_amount>"] if the amount is wrong, replacing <correct_amount> '
        "with the correct amount.\n\n"
        f"Receipt text:\n{raw_text}"
    )

    try:
        response_text = _call_gemini(prompt, config)
        if not response_text:
            return None
        return json.loads(response_text)
    except (json.JSONDecodeError, Exception):
        return None

def _call_gemini(prompt: str, config: Config) -> str | None:
    """Send a prompt to Gemini and return the raw text response."""
    if not config.llm_api_key:
        return None

    try:
        client = genai.Client(api_key=config.llm_api_key)
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt,
        )
        return response.text
    except Exception:
        return None
    