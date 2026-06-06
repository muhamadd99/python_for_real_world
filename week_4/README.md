# AutoSport-Pay: Automated Chat-Based Sports Event Payment Collector

AutoSport-Pay is an AI-powered payment verification assistant for community sports organizers. It runs on the organizer's personal Telegram account via a userbot, extracts data from receipts, validates it against bank rules, and publishes a real-time payment manifest.

---

## 📋 Problem and Solution

**Problem:** Collecting and verifying group payments is manual and error-prone. Organizers must check receipts across chats, match payer names, and detect duplicates or fraud.

**Solution:** Players send receipts directly to the organizer's Telegram account. The userbot reads incoming receipts, extracts fields, validates structure and security checks, and updates the payment status stream in real time.

---

## 🚀 Key Features

- **Frictionless UX:** Players just send a receipt. No links or bot commands.
- **Phone Contact Syncing:** Telegram address book names map directly to payer names.
- **Receipt Validation:** Structured parsing plus rule-based verification.
- **Fraud Checks:** Detects duplicate reference IDs or mismatched values.

---

## 🤖 System Architecture & AI Component

```text
                                  [ Receipt Dataset DB ]
                                  (Known Bank Fields/Keywords)
                                                 │
                                                 ▼ (Reads Rules)
[ Player App ] ──► [ Organizer TG ] ──► [ Userbot Script ] ──► [ OCR + LLM ]
                                                 │
                                         (Compares & Verifies)
                                                 │
                                                 ▼
                                     [ Real-Time Console Stream ]
                                     1. Mad PAID
                                     2. Abu PAID
                                     3. Jai FISHY
                                     ...
                                     22. Haziq NOT PAID
```

### 🔵 **Raw Data Tier**

Captures the initial, unverified document data extracted by OCR across different bank receipt layouts (Maybank, CIMB Octo, DuitNow). This is raw text before validation.

### 🥈 **Silver Data Tier: Structural Validation**

Checks formatting integrity. Ensures required fields, character counts, and structure match known bank templates.
- **Failure State:** If structures do not align, mark as `Receipt Failed`.

### 🥇 **Gold Data Tier: Security & Information Lookup**

Validates extracted fields against strict parameters and duplication rules.
- **Tracked Variables:** Bank name, reference ID keywords (e.g., *maybank reference ID*, *CIMB OCTO Reference No*), transaction date/time, and field length bounds.
- **Deduplication Check:** Rejects repeated reference IDs.
- **Suspicious State:** Mismatches (amount/date window) mark as `Receipt Fishy`.

---

## 🧾 Receipt File Support (Images and PDFs)

Receipts arrive as images or PDFs.

- **Text-based PDF:** Extract text directly.
- **Scanned/image PDF:** Convert pages to images, then run OCR.

Recommended flow: try direct PDF text extraction first, then fallback to OCR if the result is empty or noisy.

---

## 🗂️ Data Component (Receipt Archive + Receipt Dataset DB)

The data layer stores both raw receipts and a curated dataset of known receipt fields.

- **Receipt Archive:** Saves incoming receipt images/PDFs and extracted OCR text for traceability.
- **Receipt Dataset DB:** Stores known bank receipt field patterns (bank_name, receiver_name, receiver_keyword, ref_id, transaction_date, transaction_time, currency, currency_keyword). This dataset is used to improve currency and receiver detection by referencing commonly observed keywords across receipts.

This enables consistent parsing across different banks and improves fraud detection over time.

---

## 🧠 LLM Output Contract (JSON)

The AI component must return strict JSON for downstream validation and storage:

```json
{
  "bank_name": "string or null",
  "receiver_name": "string or null",
  "amount": "string or null",
  "currency": "string or null",
  "reference_id": "string or null",
  "transaction_date": "string or null",
  "transaction_time": "string or null",
  "status": "VALID | INVALID | FISHY",
  "reasons": ["string"]
}
```

---

## 🔌 Integration Flow (Telegram Userbot)

1. Listen for new private messages.
2. If a message contains an image or PDF, download it.
3. Extract text (PDF text or OCR fallback).
4. Send text to LLM parser.
5. Validate against receipt dataset rules.
6. Update the real-time payment manifest.

---

## ▶️ How to Run Locally

Prerequisite: install `uv` for environment management.

1. Create a Python 3.14 environment (backend).

```bash
cd week_4/backend
uv venv --python 3.14
source .venv/bin/activate
uv pip install -e .
```

2. Copy the environment template and fill in values.

```bash
cd ../
cp .env.example .env
```

3. Start the API server for uploads.

```bash
cd backend
uvicorn src.api:app --host 0.0.0.0 --port 8000
```

4. (Optional) Start the Telegram userbot in another terminal.

```bash
cd week_4/backend
python -m src.main
```

5. Serve the frontend upload page.

```bash
cd week_4/frontend
uv venv --python 3.14
source .venv/bin/activate
uv pip install -e .
uvicorn src.main:app --host 0.0.0.0 --port 3000
```

6. Open http://localhost:3000 and upload a receipt.

---

## 🐳 Run with Docker

```bash
cd week_4
docker compose up --build
```

Frontend: http://localhost:3000
Backend API: http://localhost:8000/receipts

---

## 🧪 Test Receipt Walkthrough

1. Send an image or PDF receipt to the organizer's Telegram account.
2. Watch the console output for a parsed JSON response.
3. Confirm the status is one of `VALID`, `INVALID`, or `FISHY`.
4. Verify the manifest updates with the payer name and status.

---

## ✅ Audience

- **Organizer:** Needs fast confirmation, duplicate checks, and status overview.
- **Teammates/Players:** Send receipt once, no extra steps.
