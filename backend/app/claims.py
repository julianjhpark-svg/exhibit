"""Split an essay into atomic claims.

The model does the work; the sentence splitter is a safety net so a provider outage produces a
degraded demo instead of a blank screen (and doubles as a third failure to show).

Check this before anything else: every downstream number depends on these 12 claims matching
data/answer_key.json. Run `python -m app.claims` to compare.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from .llm import ModelOutputError, ProviderError, chat_json
from .models import ClaimInput
from .promptlib import load_prompt
from .verify import normalize

REPO_ROOT = Path(__file__).resolve().parents[2]
MAX_CLAIMS = 30

# "et al." and friends end with a period but not a sentence.
_ABBREV = re.compile(
    r"(?:^|\s)(?:et al|e\.g|i\.e|vs|cf|approx|Fig|Eq|No|Dr|Mr|Ms|Mrs|Prof|St)\.$",
    re.IGNORECASE,
)


async def extract_claims(essay: str) -> tuple[list[ClaimInput], str]:
    """Return (claims, mode) where mode is 'model' or 'fallback'."""
    try:
        data = await chat_json(load_prompt("claim_extraction.md"), essay)
        raw = data.get("claims") or []
        claims = [
            ClaimInput(id=str(item.get("id") or f"C{i + 1:02d}"), text=str(item["text"]).strip())
            for i, item in enumerate(raw)
            if isinstance(item, dict) and str(item.get("text", "")).strip()
        ]
        if claims:
            return claims[:MAX_CLAIMS], "model"
    except (ProviderError, ModelOutputError, KeyError, TypeError, ValueError):
        pass
    return split_sentences(essay), "fallback"


def split_sentences(text: str) -> list[ClaimInput]:
    """Crude, predictable, and good enough to keep the demo alive.

    Two things that break naive splitters and are handled here:
      - "et al." / "e.g." mid-sentence (merged back into the following fragment)
      - a front-matter block above a `---` rule (dropped, as it isn't essay text)
    """
    body = re.sub(r"^#.*$", "", text, flags=re.MULTILINE)  # drop headings
    if "\n---\n" in body:
        body = body.split("\n---\n", 1)[1]

    flat = " ".join(body.split())
    merged: list[str] = []
    for part in re.split(r"(?<=[.!?])\s+", flat):
        part = part.strip()
        if not part:
            continue
        if merged and _ABBREV.search(merged[-1]):
            merged[-1] = f"{merged[-1]} {part}"
        else:
            merged.append(part)
    return [
        ClaimInput(id=f"C{i + 1:02d}", text=s) for i, s in enumerate(merged) if len(s) > 25
    ][:MAX_CLAIMS]


# ---------------------------------------------------------------- CLI

def _main(argv: list[str]) -> int:
    essay_path = Path(argv[1]) if len(argv) > 1 else REPO_ROOT / "data" / "essay_draft.md"
    key_path = REPO_ROOT / "data" / "answer_key.json"
    essay = essay_path.read_text(encoding="utf-8")
    key = json.loads(key_path.read_text(encoding="utf-8"))

    claims = split_sentences(essay)
    expected = {c["id"]: normalize(c["text"]) for c in key["claims"]}
    got = {c.id: normalize(c.text) for c in claims}

    print(f"{len(claims)} claims from {essay_path.name} (offline splitter)")
    print(f"{len(expected)} labelled in {key_path.name}\n")

    bad = 0
    for cid, text in expected.items():
        if cid not in got:
            print(f"  {cid} MISSING")
            bad += 1
        elif got[cid] != text:
            print(f"  {cid} differs")
            bad += 1
    print(f"\n{'OK - all match' if not bad else f'{bad} mismatch(es) - fix the key or the splitter'}")

    print("\nNote: this checks the offline splitter. With an API key, /api/check uses the model.")
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
