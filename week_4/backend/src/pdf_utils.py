from __future__ import annotations

from typing import Iterable
import os

from pypdf import PdfReader

from .ocr import ocr_image


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from PDF file.
    
    First attempts text extraction via pypdf.
    If no text found, converts PDF pages to images and uses OCR.
    """
    try:
        reader = PdfReader(pdf_path)
        text_chunks = []
        for page in reader.pages:
            text_chunks.append(page.extract_text() or "")
        text = "\n".join(text_chunks).strip()

        if text:
            return text
    except Exception as e:
        print(f"PDF text extraction failed: {e}. Falling back to OCR.")

    # Fallback to image-based OCR
    try:
        images = _pdf_to_images(pdf_path)
        if not images:
            raise ValueError("Could not convert PDF pages to images")

        ocr_chunks = []
        for image_path in images:
            try:
                ocr_chunks.append(ocr_image(image_path))
            finally:
                # Cleanup temporary image files
                if os.path.exists(image_path):
                    os.remove(image_path)
        
        result = "\n".join(ocr_chunks).strip()
        if not result:
            raise ValueError("OCR extraction produced no text")
        return result
    except Exception as e:
        raise RuntimeError(f"PDF processing failed: {str(e)}")


def _pdf_to_images(pdf_path: str) -> list[str]:
    """Convert PDF pages to PNG images"""
    try:
        from pdf2image import convert_from_path
    except ImportError:
        raise RuntimeError("pdf2image is required for PDF-to-image conversion")

    try:
        images = convert_from_path(pdf_path)
        image_paths = []
        for idx, image in enumerate(images, start=1):
            image_path = f"{pdf_path}.page{idx}.png"
            image.save(image_path, "PNG")
            image_paths.append(image_path)
        return image_paths
    except Exception as e:
        raise RuntimeError(f"PDF page conversion failed: {str(e)}")
