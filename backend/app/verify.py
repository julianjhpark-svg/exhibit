"""The guard. Whatever the model says, support is only real if the quote is really there.

This file is the A2 design decision in code:
  a claimed quote is string-matched against the cited page, and any mismatch is downgraded
  to `cant_verify`. That converts "the model says it's supported" into something checkable.
"""

from __future__ import annotations

import re

from .models import VerdictOut

_WS = re.compile(r"\s+")
# typographic variants that differ between a PDF and a model's copy of it
_FOLD = str.maketrans(
    {
        "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "-", "\u00ad": "", "\u00a0": " ",
    }
)


def normalize(text: str) -> str:
    return _WS.sub(" ", text.translate(_FOLD)).strip().lower()


def is_verbatim(quote: str | None, page_text: str) -> bool:
    """True when `quote` appears contiguously in `page_text`, ignoring whitespace/quotes/dashes."""
    if not quote or not page_text:
        return False
    return normalize(quote) in normalize(page_text)


def enforce(verdict: VerdictOut, page_text: str | None) -> VerdictOut:
    """Downgrade unsupported claims of support. Never upgrades anything."""
    if verdict.verdict in ("supported", "partial"):
        if not page_text or not is_verbatim(verdict.quote, page_text):
            return verdict.model_copy(
                update={
                    "verdict": "cant_verify",
                    "quote": None,
                    "page": None,
                    "downgraded": True,
                    "reason": "No verbatim match for the returned quote in the cited page.",
                }
            )
    return verdict


def tally(verdicts: list[VerdictOut]) -> dict[str, int]:
    counts = {"supported": 0, "partial": 0, "unsupported": 0, "cant_verify": 0}
    for v in verdicts:
        counts[v.verdict] += 1
    counts["total"] = len(verdicts)
    counts["downgraded"] = sum(1 for v in verdicts if v.downgraded)
    return counts
