"""Exhibit API.

Endpoints are deliberately small. `MOCK=1` serves the labels from data/answer_key.json so the
frontend can be built and demoed before the verifier exists — flip it off once /api/check is real.

Run from backend/:
    uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .extract import NoTextLayer, PdfTooLarge, extract_pages
from .models import CheckRequest, CheckResponse, Source, SourceOut, VerdictOut
from .verify import normalize, tally

REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPO_ROOT / ".env")

MOCK = os.getenv("MOCK", "1") == "1"
MAX_PDF_MB = int(os.getenv("MAX_PDF_MB", "20"))

app = FastAPI(title="Exhibit")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # local demo only
    allow_methods=["*"],
    allow_headers=["*"],
)


def load_key() -> dict:
    return json.loads((REPO_ROOT / "data" / "answer_key.json").read_text(encoding="utf-8"))


def load_essay() -> str:
    return (REPO_ROOT / "data" / "essay_draft.md").read_text(encoding="utf-8")


@app.get("/health")
def health() -> dict:
    return {"ok": True, "mock": MOCK}


@app.get("/api/demo")
def demo() -> dict:
    """The sample essay + sources, so the frontend has something to show on first load."""
    key = load_key()
    return {"essay": load_essay(), "sources": key["sources"]}


@app.post("/api/sources", response_model=SourceOut)
async def add_source(file: UploadFile = File(...)) -> SourceOut:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(415, detail={"code": "unsupported_type", "note": "PDF only for now."})

    tmp = REPO_ROOT / "runs" / f"upload_{file.filename}"
    tmp.parent.mkdir(exist_ok=True)
    tmp.write_bytes(await file.read())

    try:
        pages = extract_pages(tmp, max_mb=MAX_PDF_MB)
    except NoTextLayer as exc:
        # Failure case #1. The client keeps its existing sources; we just refuse this one.
        raise HTTPException(
            422,
            detail={
                "code": "no_text_layer",
                "note": str(exc),
                "fix": "Upload a text-based PDF, or paste the text of the pages you need.",
            },
        ) from exc
    except PdfTooLarge as exc:
        raise HTTPException(413, detail={"code": "too_large", "note": str(exc)}) from exc

    return SourceOut(
        source=Source(id=file.filename, title=file.filename, pages=len(pages), kind="upload"),
        pages=len(pages),
        chars=sum(len(p.text) for p in pages),
        usable=True,
    )


@app.post("/api/check", response_model=CheckResponse)
def check(req: CheckRequest) -> CheckResponse:
    """TODO: replace the mock branch with the real pipeline.

    Intended pipeline (see prompts/verification.md):
        1. claim extraction      -> prompts/claim_extraction.md  (or reuse req.claims)
        2. retrieve top-k        -> extract.passages_from() + BM25 or embeddings
        3. one model call/claim  -> quote-or-abstain
        4. verify.enforce()      -> downgrade fabricated quotes
        5. tally()               -> counts for the header
    """
    warnings: list[str] = []
    if not req.sources:
        warnings.append("No sources attached — every claim will be 'can't verify'.")

    if MOCK:
        key = load_key()
        by_text = {normalize(c["text"]): c for c in key["claims"]}
        claims: list[VerdictOut] = []
        for line in _split_sentences(req.essay):
            match = by_text.get(normalize(line))
            if match:
                claims.append(
                    VerdictOut(
                        claim_id=match["id"],
                        verdict=match["expected"],
                        quote="(mock) " + (match["quote_must_contain"][0] if match["quote_must_contain"] else ""),
                        source_id=match["expected_source"],
                        page=None,
                        reason=match["notes"],
                    )
                )
            else:
                claims.append(VerdictOut(claim_id=f"X{len(claims) + 1:02d}", verdict="cant_verify"))
        return CheckResponse(claims=claims, stats=tally(claims), warnings=warnings)

    raise HTTPException(
        501,
        detail={
            "code": "not_implemented",
            "note": "Set MOCK=1 for the UI, or wire the pipeline described in app.check().",
        },
    )


@app.post("/api/quiz")
def quiz() -> dict:
    """TODO: build from supported claims only. See prompts/quiz.md."""
    return {"quiz": [], "note": "Not implemented yet — build from supported claims only."}


def _split_sentences(text: str) -> list[str]:
    """Placeholder splitter for mock mode. Real extraction belongs in the model call."""
    out: list[str] = []
    for raw in text.replace("\n", " ").split(". "):
        s = raw.strip()
        if len(s) > 30:
            out.append(s + ("" if s.endswith(".") else "."))
    return out
