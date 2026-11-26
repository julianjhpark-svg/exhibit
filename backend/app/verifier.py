"""Verify one claim: the model proposes, the guard decides.

Order matters. We record whether the model's quote was *already* verbatim (`raw_ok`) before
`enforce()` runs, because that difference is the measurable contribution of the guard:
"the model quoted correctly 11/12 times; the one paraphrase was caught and downgraded."
"""

from __future__ import annotations

from typing import Callable

from .llm import ProviderError, chat_json
from .models import ClaimInput, VerdictOut
from .promptlib import load_prompt
from .retrieve import Chunk
from .verify import enforce, is_verbatim

VALID = {"supported", "partial", "unsupported", "cant_verify"}
MAX_PASSAGE_CHARS = 1400

PageLookup = Callable[[str | None, int | None], str | None]


def build_user(claim: ClaimInput, passages: list[Chunk]) -> str:
    blocks = [
        f"[{i + 1}] {p.source_id} p.{p.page}\n{p.text[:MAX_PASSAGE_CHARS]}"
        for i, p in enumerate(passages)
    ]
    return f"CLAIM: {claim.text}\n\nPASSAGES:\n" + "\n\n".join(blocks)


async def verify_claim(
    claim: ClaimInput, passages: list[Chunk], page_lookup: PageLookup
) -> tuple[VerdictOut, bool]:
    """Return (verdict, quote_was_verbatim_before_enforcement)."""
    if not passages:
        return VerdictOut(
            claim_id=claim.id,
            verdict="cant_verify",
            reason="No passages retrieved for this claim.",
        ), False

    try:
        data = await chat_json(load_prompt("verification.md"), build_user(claim, passages))
    except ProviderError as exc:
        # Failure #2: the service is unavailable. Say so per claim; don't lose the run.
        return VerdictOut(
            claim_id=claim.id, verdict="cant_verify", reason=f"Verifier unavailable: {exc}"
        ), False

    verdict = str(data.get("verdict", "")).strip().lower()
    if verdict not in VALID:
        verdict = "cant_verify"

    quote = data.get("quote")
    quote = quote.strip() if isinstance(quote, str) and quote.strip() else None

    page = data.get("page")
    try:
        page = int(page) if page is not None else None
    except (TypeError, ValueError):
        page = None

    source_id = data.get("source_id")
    source_id = str(source_id) if source_id else None

    out = VerdictOut(
        claim_id=claim.id,
        verdict=verdict,
        quote=quote,
        source_id=source_id,
        page=page,
        reason=(str(data.get("reason") or "")[:400] or None),
    )

    page_text = page_lookup(source_id, page)
    raw_ok = bool(quote) and is_verbatim(quote, page_text or "")
    out = enforce(out, page_text)

    if out.verdict in ("supported", "partial") and page_text:
        out.page_text = page_text  # the UI highlights the quote inside this
    return out, raw_ok
