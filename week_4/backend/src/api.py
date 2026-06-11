from __future__ import annotations

import os
from pathlib import Path as FilePath

from fastapi import FastAPI, File, Form, HTTPException, Path, UploadFile
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from .config import Config
from .processor import process_receipt
from .storage import Storage


load_dotenv()

app = FastAPI(title="AutoSport-Pay API")

config = Config.from_env()
storage = Storage(config.database_path)
storage.init_schema()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

@app.get("/receipts")
def list_receipts() -> JSONResponse:
    receipts = storage.get_all_receipts()
    return JSONResponse(receipts)

@app.delete("/receipts/all")
def delete_all_receipts() -> JSONResponse:
    count = storage.delete_all_receipts()
    return JSONResponse({"status": "ok", "message": f"Deleted {count} receipts."})

@app.post("/receipts")
async def upload_receipt(file: UploadFile = File(...), sender: str = Form("web")) -> JSONResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="missing filename")

    upload_dir = FilePath("./data/receipts")
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / file.filename
    content = await file.read()
    file_path.write_bytes(content)

    try:
        parsed = process_receipt(str(file_path), sender, storage, config)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return JSONResponse(parsed)

@app.delete("/receipts/{receipt_id}")
def delete_receipt(receipt_id: int = Path(..., ge=1)) -> JSONResponse:
    if storage.delete_receipt(receipt_id):
        return JSONResponse({"status": "ok", "message": f"Receipt {receipt_id} deleted."})
    raise HTTPException(status_code=404, detail=f"Receipt {receipt_id} not found.")
