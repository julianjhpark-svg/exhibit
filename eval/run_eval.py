"""Score Exhibit against data/answer_key.json and write eval/results.md.

This is the A3 evidence. Run it after every prompt change; paste the table into Devpost.

    python eval/run_eval.py --mock          # sanity-check the harness itself, no server needed
    python eval/run_eval.py                 # score the running app at localhost:8000
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
KEY = json.loads((REPO / "data" / "answer_key.json").read_text(encoding="utf-8"))
ESSAY = (REPO / KEY["essay"]).read_text(encoding="utf-8")
LABELS = KEY["verdict_enum"]


def predict_mock() -> dict[str, str]:
    """Return the ground truth as if it were a prediction — proves the scorer works."""
    return {c["id"]: c["expected"] for c in KEY["claims"]}


def predict_live(base_url: str) -> tuple[dict[str, str], list[dict]]:
    import urllib.request

    body = json.dumps({"essay": ESSAY, "sources": KEY["sources"]}).encode()
    req = urllib.request.Request(
        f"{base_url}/api/check", data=body, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read())
    except Exception as exc:  # noqa: BLE001 — a failed eval run is still a result worth showing
        sys.exit(f"Could not reach {base_url}/api/check: {exc}")

    preds = {v["claim_id"]: v["verdict"] for v in data.get("claims", [])}
    return preds, data.get("claims", [])


def quote_fidelity(verdicts: list[dict]) -> tuple[int, int]:
    """How many returned quotes actually appear in the cited page text (string match)."""
    try:
        from pypdf import PdfReader
    except ImportError:
        return (0, 0)

    page_cache: dict[tuple[str, int], str] = {}
    checked = verbatim = 0

    def page_text(source_id: str, page: int) -> str:
        nonlocal page_cache
        if (source_id, page) not in page_cache:
            src = next((s for s in KEY["sources"] if s["id"] == source_id), None)
            path = REPO / src["pdf"] if src else None
            text = ""
            if path and path.exists():
                reader = PdfReader(str(path))
                if 0 < page <= len(reader.pages):
                    text = reader.pages[page - 1].extract_text() or ""
            page_cache[(source_id, page)] = " ".join(text.split()).lower()
        return page_cache[(source_id, page)]

    for v in verdicts:
        if not v.get("quote") or not v.get("source_id") or not v.get("page"):
            continue
        checked += 1
        if " ".join(v["quote"].split()).lower() in page_text(v["source_id"], v["page"]):
            verbatim += 1
    return verbatim, checked


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true", help="score ground truth against itself")
    ap.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = ap.parse_args()

    if args.mock:
        preds, verdicts = predict_mock(), []
        note = "Mock run: predictions are the ground truth. This checks the scorer, not the model."
    else:
        preds, verdicts = predict_live(args.base_url)
        note = f"Live run against {args.base_url}."

    rows, correct = [], 0
    for claim in KEY["claims"]:
        p = preds.get(claim["id"], "MISSING")
        ok = p == claim["expected"]
        correct += ok
        rows.append((claim["id"], claim["expected"], p, "pass" if ok else "FAIL"))

    total = len(KEY["claims"])
    abstain_targets = [c for c in KEY["claims"] if c["expected"] in ("unsupported", "cant_verify")]
    abstained = sum(1 for c in abstain_targets if preds.get(c["id"]) != "supported")
    lenient = sum(
        1
        for c in KEY["claims"]
        if c["expected"] in ("partial", "unsupported") and preds.get(c["id"]) == "supported"
    )
    vb, checked = quote_fidelity(verdicts) if verdicts else (0, 0)

    lines = [
        "# Exhibit — evaluation results",
        "",
        f"_{note}_",
        "",
        f"- **Verdict accuracy:** {correct}/{total} ({100 * correct / total:.0f}%)",
        f"- **Abstention:** {abstained}/{len(abstain_targets)} unsupported claims were not marked supported",
        f"- **Over-credulity:** {lenient} claim(s) called supported when they were partial/unsupported",
        f"- **Quote fidelity:** {vb}/{checked} returned quotes found verbatim in the cited page"
        if checked
        else "- **Quote fidelity:** not measured (PDFs missing — run scripts/fetch_sources.py)",
        "",
        "| Claim | Expected | Predicted | |",
        "|---|---|---|---|",
    ]
    lines += [f"| {i} | {e} | {p} | {r} |" for i, e, p, r in rows]
    lines += [
        "",
        "## What this establishes",
        "",
        "Reliable for: <fill in — e.g. expository prose with a clean text layer>.",
        "Degrades on: <fill in — e.g. tables, and claims needing synthesis across two sources>.",
        "",
        "## Confusion",
        "",
        "```",
        *[f"{k:>12}: {v}" for k, v in Counter(p for _, _, p, _ in rows).items()],
        "```",
    ]

    out = REPO / "eval" / "results.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:14]))
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
