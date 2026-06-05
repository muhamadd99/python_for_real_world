from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .config import Config
from .processor import process_receipt
from .storage import Storage


load_dotenv()

app = FastAPI(title="AutoSport-Pay API", version="0.1.0")

# Add CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

config = Config.from_env()
storage = Storage(config.database_path)
storage.init_schema()


@app.get("/health")
def health() -> dict:
    """Health check endpoint"""
    return {"status": "ok", "service": "autosport-pay-backend"}


@app.post("/receipts")
async def upload_receipt(file: UploadFile = File(...), sender: str = "web") -> JSONResponse:
    """
    Upload and process a receipt file (image or PDF).
    
    Returns extracted receipt data including receiver name, amount, date, and reference ID.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="missing filename")
    
    # Validate file extension
    valid_extensions = {".pdf", ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in valid_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Supported: {', '.join(valid_extensions)}"
        )

    upload_dir = Path("./data/receipts")
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / file.filename
    try:
        content = await file.read()
        file_path.write_bytes(content)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"File write error: {str(exc)}") from exc

    try:
        parsed = process_receipt(str(file_path), sender, storage, config)
        return JSONResponse(parsed)
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"error": str(exc), "status": "ERROR"}
        )


@app.get("/receipts/{receipt_id}")
async def get_receipt(receipt_id: str) -> JSONResponse:
    """Retrieve a previously processed receipt by ID"""
    try:
        receipt = storage.get_receipt(receipt_id)
        if not receipt:
            raise HTTPException(status_code=404, detail="Receipt not found")
        return JSONResponse(receipt)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
