from __future__ import annotations

import sys
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
    ref_keyword = _find_ref_keyword(text)
    reference_id = _find_reference_id(text, ref_keyword)
    date = _find_date(text)
    time = _find_time(text)

    return {
        "bank_name": bank_name,
        "receiver_name": receiver_name,
        "receiver_keyword": receiver_keyword,
        "amount": amount,
        "currency": _find_currency(text),
        "reference_id": reference_id,
        "ref_keyword": ref_keyword,
        "transaction_date": date,
        "transaction_time": time,
    }

def _find_bank_name(text: str) -> str | None:
    
    match = re.search(r"((?:[\w\s]+?)\s+bank|bank\s+(?:[\w\s]+?))", text, re.IGNORECASE)
    if match:
        return match.group(1).strip().title()
    candidates = ["maybank", "cimb", "public bank", "rhb", "hsbc"]
    lower = text.lower()
    for name in candidates:
        if name in lower:
            return name.title()
    return None

def _find_amount(text: str) -> str | None:
    # First try: require .00 decimals
    match = re.search(r"(RM|MYR)\s?([0-9]+\.[0-9]{2})", text, re.IGNORECASE)
    if match:
        return match.group(2)
    
    # Fallback: accept whole numbers too
    match = re.search(r"(RM|MYR)\s?([0-9]+)", text, re.IGNORECASE)
    if match:
        return match.group(2)
    return None


def _find_currency(text: str) -> str | None:
    if re.search(r"\bRM\b|\bMYR\b", text, re.IGNORECASE):
        return "MYR"
    return None

def _find_reference_id(text: str, ref_keyword: str | None = None) -> str | None:
    # If we found a ref_keyword, use it to locate the reference ID dynamically
    if ref_keyword:
        # Use the ref_keyword directly — escape it and search for the ID value after it
        escaped = re.escape(ref_keyword)
        # Build pattern: keyword followed by optional separator then the ID value
        pattern = escaped + r"\s*[.:\s]*\s*([A-Za-z0-9\-]{6,})"
        print(f"[DEBUG ref_id] pattern='{pattern}'", file=sys.stderr, flush=True)
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            print(f"[DEBUG ref_id] found via ref_keyword='{ref_keyword}' → '{match.group(1)}'", file=sys.stderr, flush=True)
            return match.group(1)
        print(f"[DEBUG ref_id] ref_keyword='{ref_keyword}' found no ID, trying fallback", file=sys.stderr, flush=True)

    return None

def _find_ref_keyword(text: str) -> str | None:
    """Find the keyword/label that precedes a reference ID.

    Strategy:
    1. Find long words (>7 chars) that are either:
       a) alphanumeric with both letters AND digits (e.g. 'TXN2024001')
       b) purely numeric with 6+ digits (e.g. '241394784')
       — these are likely the reference ID values.
    2. For each such value, look at the text before it on the same line to
       extract the descriptive keyword/label (e.g. 'Reference No.', 'Ref', 'OCTO Reference No.').
    3. Returns the longest such label found.
    """
    # Find all long words (likely ref ID values): alphanumeric with letters+digits, or pure digit strings
    ref_id_values = []
    # Alphanumeric words with both letters and digits (8+ chars)
    for m in re.finditer(r"\b([A-Za-z0-9]{8,})\b", text):
        w = m.group(1)
        if re.search(r"[A-Za-z]", w) and re.search(r"\d", w):
            ref_id_values.append((w, m.start()))
    # Pure digit strings (6+ digits) — e.g. '241394784'
    for m in re.finditer(r"\b(\d{6,})\b", text):
        ref_id_values.append((m.group(1), m.start()))

    candidates = []
    for ref_val, pos in ref_id_values:
        if pos <= 0:
            continue
        # Get the text before this ref value (up to 50 chars)
        before = text[max(0, pos - 50):pos].strip()
        # Extract the last word/phrase before the ref value as the keyword
        # e.g. "OCTO Reference No." or "Reference No:" or "Ref."
        label_match = re.search(r"([A-Za-z][A-Za-z0-9 .#:\-]{1,30}?[:.]?)\s*$", before)
        if label_match:
            keyword = label_match.group(1).strip()
            if len(keyword) >= 2:
                candidates.append(keyword)
                print(f"[DEBUG ref_keyword] ref_val='{ref_val}' keyword='{keyword}'", file=sys.stderr, flush=True)

    if candidates:
        best = max(candidates, key=len)
        print(f"[DEBUG ref_keyword] best='{best}'", file=sys.stderr, flush=True)
        return best
    print("[DEBUG ref_keyword] no match", file=sys.stderr, flush=True)
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
            match = re.search(pattern, text)
            # DEBUG START
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
    # Fallback: find a line with 20+ chars containing only letters and spaces
    # (no numbers, no :, no /) — likely a receiver name line.
    # Return the preceding line as the keyword, and the long line as the name.
    lines = text.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if len(stripped) >= 20 and re.match(r"^[A-Za-z ]+$", stripped):
            keyword = lines[i - 1].strip() if i > 0 else ""
            print(f"[DEBUG receiver_keyword] fallback keyword='{keyword}' name='{stripped}'", file=sys.stderr, flush=True)
            return keyword, stripped

    return None, None

def confirm_amount_with_ai(parsed: dict, raw_text: str, config: Config) -> dict:
    """Use LLM to confirm the regex-extracted amount, receiver name, and reference ID."""
    if config.llm_provider.lower() == "mock":
        parsed["amount_confirmed"] = None
        return parsed

    regex_amount = parsed.get("amount")
    regex_receiver = parsed.get("receiver_name")
    regex_ref_id = parsed.get("reference_id")

    if not regex_amount and not regex_receiver and not regex_ref_id:
        return parsed  # nothing to confirm

    result = _ask_llm_for_fields(regex_amount, regex_receiver, regex_ref_id, raw_text, config)

    if result is None:
        parsed["amount_confirmed"] = None
        parsed.setdefault("reasons", [])
        parsed["reasons"].append("llm_confirmation_failed: LLM returned no response")
        return parsed

    is_fishy = result.get("fishy", False)
    parsed["llm_fishy"] = is_fishy

    all_confirmed = True

    # Check amount
    amount_result = result.get("amount", {})
    if amount_result.get("confirmed"):
        parsed["amount_confirmed"] = True
        parsed["amount_llm_value"] = regex_amount
    else:
        all_confirmed = False
        parsed["amount_confirmed"] = False
        parsed.setdefault("reasons", [])
        parsed["status"] = "FISHY"
        llm_amount = amount_result.get("value")
        if llm_amount:
            parsed["amount_llm_value"] = llm_amount
            parsed["amount_regex"] = regex_amount
            parsed["amount"] = llm_amount
            parsed["reasons"].append(f"amount_mismatch: regex={regex_amount}, llm={llm_amount}")
        else:
            parsed["amount_llm_value"] = None
            parsed["reasons"].append("amount_mismatch: LLM could not confirm amount")

    # Check receiver
    receiver_result = result.get("receiver", {})
    if receiver_result.get("confirmed"):
        parsed["receiver_confirmed"] = True
    else:
        all_confirmed = False
        parsed["receiver_confirmed"] = False
        parsed.setdefault("reasons", [])
        parsed["status"] = "FISHY"
        llm_receiver = receiver_result.get("value")
        if llm_receiver:
            parsed["receiver_llm_value"] = llm_receiver
            parsed["receiver_regex"] = regex_receiver
            parsed["receiver_name"] = llm_receiver
            parsed["reasons"].append(f"receiver_mismatch: regex={regex_receiver}, llm={llm_receiver}")
        else:
            parsed["receiver_llm_value"] = None
            parsed["reasons"].append("receiver_mismatch: LLM could not confirm receiver")

    # Check ref_id
    ref_result = result.get("ref_id", {})
    if ref_result.get("confirmed"):
        parsed["ref_id_confirmed"] = True
    else:
        all_confirmed = False
        parsed["ref_id_confirmed"] = False
        parsed.setdefault("reasons", [])
        parsed["status"] = "FISHY"
        llm_ref = ref_result.get("value")
        if llm_ref:
            parsed["ref_id_llm_value"] = llm_ref
            parsed["ref_id_regex"] = regex_ref_id
            parsed["reference_id"] = llm_ref
            parsed["reasons"].append(f"ref_id_mismatch: regex={regex_ref_id}, llm={llm_ref}")
        else:
            parsed["ref_id_llm_value"] = None
            parsed["reasons"].append("ref_id_mismatch: LLM could not confirm ref_id")

    if all_confirmed:
        parsed["status"] = "VALID"
    elif not is_fishy:
        # LLM said not fishy but something didn't match — still mark valid
        parsed["status"] = "VALID"

    return parsed


def _ask_llm_for_fields(regex_amount: str | None, regex_receiver: str | None,
                         regex_ref_id: str | None, raw_text: str, config: Config) -> dict | None:
    """Ask LLM to confirm amount, receiver name, and reference ID.

    Returns a dict like:
    {
        "amount": {"confirmed": true, "value": null},
        "receiver": {"confirmed": true, "value": null},
        "ref_id": {"confirmed": false, "value": "correct_ref_id"}
    }
    """
    prompt = (
        "A bank receipt was parsed and the following fields were extracted:\n"
        f"- Amount: {regex_amount or 'not found'}\n"
        f"- Receiver Name: {regex_receiver or 'not found'}\n"
        f"- Reference ID: {regex_ref_id or 'not found'}\n\n"
        "Step 1: Check if any of these 3 fields look fishy, suspicious, or potentially wrong.\n"
        "Consider things like:\n"
        "- Amount seems too round, too small, or doesn't match typical transaction patterns\n"
        "- Receiver name looks incomplete, garbled, or contains strange characters\n"
        "- Reference ID looks malformed, too short, or suspicious\n\n"
        "Step 2: If ANY field looks fishy, review the receipt text below to verify and correct it.\n"
        "If NOTHING looks fishy, just confirm all fields as correct.\n\n"
        "Respond with a JSON object in this exact format:\n"
        '{\n'
        '  "fishy": true or false,\n'
        '  "amount": {"confirmed": true or false, "value": null or "<correct_amount>"},\n'
        '  "receiver": {"confirmed": true or false, "value": null or "<correct_receiver>"},\n'
        '  "ref_id": {"confirmed": true or false, "value": null or "<correct_ref_id>"}\n'
        '}\n\n'
        "Rules:\n"
        '- Set "fishy": true if anything looks suspicious, false if all looks normal.\n'
        '- Set "confirmed": true if the extracted value looks correct.\n'
        '- Set "confirmed": false if wrong, and put the correct value in "value".\n'
        '- Set "value": null if confirmed or if you cannot determine the correct value.\n\n'
        f"Receipt text (only review if something looks fishy):\n{raw_text}"
    )

    try:
        response_text = _call_gemini(prompt, config)
        if not response_text:
            return None
        text = response_text.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            # remove first line (```json) and last line (```)
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines).strip()
        return json.loads(text)
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
    except Exception as e:
        print(f"[ERROR] Gemini call failed: {e}", file=sys.stderr, flush=True)
        return None
    