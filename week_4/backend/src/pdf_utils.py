from __future__ import annotations

from typing import Iterable

from pypdf import PdfReader

from .ocr import ocr_image


def extract_text_from_pdf(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    text_chunks = []
    for page in reader.pages:
        text_chunks.append(page.extract_text() or "")
    text = "\n".join(text_chunks).strip()

    if text:
        return text

    images = _pdf_to_images(pdf_path)
    if not images:
        return ""

    ocr_chunks = []
    for image_path in images:
        ocr_chunks.append(ocr_image(image_path))
    return "\n".join(ocr_chunks).strip()


def _pdf_to_images(pdf_path: str) -> list[str]:
    try:
        from pdf2image import convert_from_path
    except ImportError:
        return []

    images = convert_from_path(pdf_path)
    image_paths = []
    for idx, image in enumerate(images, start=1):
        image_path = f"{pdf_path}.page{idx}.png"
        image.save(image_path, "PNG")
        image_paths.append(image_path)
    return image_paths
