from __future__ import annotations

import os
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

app = FastAPI(title="AutoSport-Pay Frontend")

assets_dir = BASE_DIR / "assets"
app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")


@app.get("/")
async def index() -> HTMLResponse:
    return HTMLResponse((BASE_DIR / "index.html").read_text(encoding="utf-8"))

@app.get("/health")
def health() -> dict:
    return {"status": "ok", "backend": BACKEND_URL}

@app.get("/api/receipts")
async def proxy_list_receipts() -> list:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(f"{BACKEND_URL}/receipts")
    return response.json()

@app.post("/api/receipts")
async def proxy_receipt(file: UploadFile = File(...), sender: str = "web") -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="missing filename")

    content = await file.read()
    files = {"file": (file.filename, content, file.content_type)}
    data = {"sender": sender}

    async with httpx.AsyncClient(timeout=180) as client:
        response = await client.post(f"{BACKEND_URL}/receipts", files=files, data=data)

    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return response.json()
