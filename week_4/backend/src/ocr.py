from __future__ import annotations

from typing import Any


def ocr_image(image_path: str) -> str:
    try:
        from PIL import Image, ImageEnhance
    except ImportError as exc:
        raise RuntimeError("Pillow is required for image OCR") from exc

    try:
        import pytesseract
    except ImportError as exc:
        raise RuntimeError("pytesseract is required for OCR") from exc

    image = Image.open(image_path)
    
    image = image.resize((image.width * 2, image.height * 2), Image.LANCZOS) #modify

    # Convert to grayscale
    image = image.convert("L") #modify

    # Increase contrast
    enhancer = ImageEnhance.Contrast(image) #modify
    image = enhancer.enhance(2.0) #modify

    return pytesseract.image_to_string(image)
