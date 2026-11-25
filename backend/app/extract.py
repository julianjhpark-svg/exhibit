"""PDF text extraction with the one check that matters: does this file have a text layer?

Failure case #1 for the demo lives here — a scanned PDF must be detected *before* the model
ever sees it, and must not wipe out the sources already loaded.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

# A page with fewer than this many characters is almost certainly image-only.
MIN_CHARS_PER_PAGE = 200


@dataclass
class Page:
    number: int  # 1-based, matches what a reader sees
    text: str


class NoTextLayer(Exception):
    """Raised when a PDF has no extractable text. Surfaced to the user as a clear warning."""


class PdfTooLarge(Exception):
    pass


def extract_pages(path: str | Path, max_mb: int = 20) -> list[Page]:
    path = Path(path)
    if path.stat().st_size > max_mb * 1024 * 1024:
        raise PdfTooLarge(f"{path.name} is larger than {max_mb} MB")

    reader = PdfReader(str(path))
    if reader.is_encrypted:
        raise NoTextLayer(f"{path.name} is password-protected")

    pages = [
        Page(number=i + 1, text=(page.extract_text() or "").strip())
        for i, page in enumerate(reader.pages)
    ]
    if looks_scanned(pages):
        raise NoTextLayer(f"{path.name} has no text layer (probably a scan)")
    return pages


def looks_scanned(pages: list[Page]) -> bool:
    """Median characters per page, not mean — one title page shouldn't decide it."""
    if not pages:
        return True
    return statistics.median(len(p.text) for p in pages) < MIN_CHARS_PER_PAGE


def passages_from(pages: list[Page], source_id: str, window: int = 900) -> list[dict]:
    """Very small chunker: ~900 characters with no overlap.

    Good enough to start. If retrieval quality disappoints, try paragraph splitting, then
    re-measure with eval/run_eval.py — do not tune blind.
    """
    out: list[dict] = []
    for page in pages:
        text = page.text
        for start in range(0, len(text), window):
            chunk = text[start : start + window].strip()
            if len(chunk) >= 80:
                out.append({"source_id": source_id, "page": page.number, "text": chunk})
    return out
