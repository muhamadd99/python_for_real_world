from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
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


@app.post("/receipts")
async def upload_receipt(file: UploadFile = File(...), sender: str = "web") -> JSONResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="missing filename")

    upload_dir = Path("./data/receipts")
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / file.filename
    content = await file.read()
    file_path.write_bytes(content)

    try:
        parsed = process_receipt(str(file_path), sender, storage, config)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return JSONResponse(parsed)
