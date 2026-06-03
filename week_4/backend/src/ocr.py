from __future__ import annotations

from typing import Any


def ocr_image(image_path: str) -> str:
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Pillow is required for image OCR") from exc

    try:
        import pytesseract
    except ImportError as exc:
        raise RuntimeError("pytesseract is required for OCR") from exc

    image = Image.open(image_path)
    return pytesseract.image_to_string(image)
