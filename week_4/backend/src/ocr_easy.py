from __future__ import annotations

import easyocr

_reader = None


def _get_reader() -> easyocr.Reader:
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(["en"], gpu=False)
    return _reader


def ocr_image_easyocr(image_path: str) -> str:
    reader = _get_reader()
    results = reader.readtext(image_path)
    lines = [text for (_, text, _conf) in results]
    return "\n".join(lines)
