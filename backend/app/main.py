"""Exhibit API.

`MOCK=1` serves the labels from data/answer_key.json so the frontend can be built and demoed
before any model call. With `MOCK=0` and a key in .env, `/api/check` runs the real pipeline:

    sources -> page text -> BM25 top-8 -> quote-or-abstain -> enforce() -> tally

Run from backend/:
    uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .claims import extract_claims, split_sentences
from .extract import NoTextLayer, Page, PdfTooLarge, extract_pages
from .models import CheckRequest, CheckResponse, Source, SourceOut, VerdictOut
from .retrieve import build_index
from .verifier import verify_claim
from .verify import normalize, tally

REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPO_ROOT / ".env")

MOCK = os.getenv("MOCK", "1") == "1"
MAX_PDF_MB = int(os.getenv("MAX_PDF_MB", "20"))
MAX_CONCURRENCY = int(os.getenv("MAX_CONCURRENCY", "4"))
TOP_K = int(os.getenv("TOP_K", "8"))

app = FastAPI(title="Exhibit")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # local demo only
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------- data

def load_key() -> dict:
    return json.loads((REPO_ROOT / "data" / "answer_key.json").read_text(encoding="utf-8"))


def load_essay() -> str:
    return (REPO_ROOT / "data" / "essay_draft.md").read_text(encoding="utf-8")


def resolve_pdf(source: Source) -> Path | None:
    """Find a source's PDF: explicit path, then data/sources, then an earlier upload."""
    if source.pdf:
        path = REPO_ROOT / source.pdf
        if path.is_file():
            return path
    for candidate in (
        REPO_ROOT / "data" / "sources" / f"{source.id}.pdf",
        REPO_ROOT / "runs" / f"upload_{source.id}",
    ):
        if candidate.is_file():
            return candidate
    for pattern_dir in (REPO_ROOT / "data" / "sources", REPO_ROOT / "runs"):
        if pattern_dir.is_dir():
            for match in pattern_dir.glob(f"*{source.id}*"):
                if match.is_file():
                    return match
    return None


def load_pages(sources: list[Source], warnings: list[str]) -> dict[str, list[Page]]:
    """Read every source. One bad file must not take the others down (failure #1)."""
    loaded: dict[str, list[Page]] = {}
    for source in sources:
        path = resolve_pdf(source)
        if path is None:
            warnings.append(f"{source.id}: PDF not found — run scripts/fetch_sources.py")
            continue
        try:
            loaded[source.id] = extract_pages(path, max_mb=MAX_PDF_MB)
        except NoTextLayer as exc:
            warnings.append(f"{source.id}: {exc}. Upload a text-based PDF or paste the text.")
        except PdfTooLarge as exc:
            warnings.append(f"{source.id}: {exc}")
        except Exception as exc:  # corrupt file, encryption we didn't catch, etc.
            warnings.append(f"{source.id}: could not be read ({type(exc).__name__})")
    return loaded


def make_lookup(loaded: dict[str, list[Page]]):
    def lookup(source_id: str | None, page: int | None) -> str | None:
        pages = loaded.get(source_id) if source_id else None
        if not pages or page is None or not 1 <= page <= len(pages):
            return None
        return pages[page - 1].text

    return lookup


# ---------------------------------------------------------------- endpoints

@app.get("/health")
def health() -> dict:
    return {"ok": True, "mock": MOCK, "concurrency": MAX_CONCURRENCY, "top_k": TOP_K}


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
        source=Source(
            id=file.filename,
            title=file.filename,
            pages=len(pages),
            kind="upload",
            pdf=str(tmp.relative_to(REPO_ROOT)),
        ),
        pages=len(pages),
        chars=sum(len(p.text) for p in pages),
        usable=True,
    )


@app.post("/api/check", response_model=CheckResponse)
async def check(req: CheckRequest) -> CheckResponse:
    warnings: list[str] = []
    if not req.sources:
        warnings.append("No sources attached — every claim will be 'can't verify'.")
    if MOCK:
        return _check_mock(req, warnings)
    return await _check_live(req, warnings)


@app.post("/api/quiz")
def quiz() -> dict:
    """TODO: build from supported claims only. See prompts/quiz.md."""
    return {"quiz": [], "note": "Not implemented yet — build from supported claims only."}


# ---------------------------------------------------------------- pipeline

async def _check_live(req: CheckRequest, warnings: list[str]) -> CheckResponse:
    loaded = load_pages(req.sources, warnings)
    if not loaded:
        return CheckResponse(claims=[], stats=tally([]), warnings=warnings)

    index = build_index(loaded)
    claims, mode = await extract_claims(req.essay)
    if mode == "fallback":
        warnings.append("Claim extraction fell back to sentence splitting (provider unavailable).")

    lookup = make_lookup(loaded)
    sem = asyncio.Semaphore(MAX_CONCURRENCY)
    circuit = {"open": False}  # stop hammering a provider we know is down

    async def one(claim):
        async with sem:
            # Check inside the semaphore so claims that were only *queued* are skipped too.
            if circuit["open"]:
                return VerdictOut(
                    claim_id=claim.id,
                    verdict="cant_verify",
                    reason="Skipped: the verifier was unavailable earlier in this run.",
                ), False
            result = await verify_claim(claim, index.top_k(claim.text, TOP_K), lookup)
        if (result[0].reason or "").startswith("Verifier unavailable"):
            if not circuit["open"]:
                warnings.append("Verifier stopped responding — remaining claims were not checked.")
            circuit["open"] = True
        return result

    pairs = await asyncio.gather(*(one(c) for c in claims))
    verdicts = [verdict for verdict, _ in pairs]
    raw_ok = sum(1 for _, ok in pairs if ok)

    stats = tally(verdicts)
    stats["claims"] = len(verdicts)
    stats["quote_ok_before_guard"] = raw_ok

    if raw_ok < sum(1 for v in verdicts if v.quote):
        warnings.append("At least one returned quote was not verbatim and was downgraded.")

    return CheckResponse(claims=verdicts, stats=stats, warnings=warnings)


def _check_mock(req: CheckRequest, warnings: list[str]) -> CheckResponse:
    key = load_key()
    by_text = {normalize(c["text"]): c for c in key["claims"]}
    verdicts: list[VerdictOut] = []
    for claim in split_sentences(req.essay):
        match = by_text.get(normalize(claim.text))
        if match:
            verdicts.append(
                VerdictOut(
                    claim_id=match["id"],
                    verdict=match["expected"],
                    source_id=match["expected_source"],
                    reason=match["notes"],
                )
            )
        else:
            verdicts.append(
                VerdictOut(claim_id=claim.id, verdict="cant_verify", reason="Not in answer key.")
            )
    return CheckResponse(claims=verdicts, stats=tally(verdicts), warnings=warnings)
