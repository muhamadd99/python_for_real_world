from __future__ import annotations

from typing import Any


def ocr_image(image_path: str) -> str:
    """
    Extract text from an image file using Tesseract OCR.
    
    Supports: PNG, JPG, JPEG, GIF, BMP, TIFF
    """
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Pillow is required for image OCR. Install: pip install pillow") from exc

    try:
        import pytesseract
    except ImportError as exc:
        raise RuntimeError("pytesseract is required for OCR. Install: pip install pytesseract") from exc

    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)
        return text.strip()
    except FileNotFoundError:
        raise FileNotFoundError(f"Image file not found: {image_path}")
    except Exception as e:
        raise RuntimeError(f"OCR processing failed for {image_path}: {str(e)}")
