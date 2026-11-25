# Exhibit — *[citation needed]*

**A citation checker that shows you what the source actually says — or admits it can't.**

Paste an essay, add its sources. Exhibit splits the essay into claims and gives each one a
verdict (**supported / partial / unsupported / can't verify**) with the verbatim sentence and
page that backs it up — or an explicit refusal when nothing does.

> Status: scaffold. The happy path is stubbed; see `docs/PLAN.md` for what to build and when.

---

## The problem

Students are told to "cite sources," then graded by a model (or a tired TA) that cannot tell a
real citation from an invented one. A citation that *looks* correct is the cheapest failure in
writing. Existing checks go the wrong direction: they generate citations, rather than proving
that a cited sentence is actually in the cited paper.

## What it does

1. **Add sources** — upload a PDF, paste a URL, or paste text. Each page keeps its page number.
2. **Check** — the essay is split into atomic claims; each claim is matched against retrieved
   passages from *your* sources only.
3. **Verdict** — supported / partial / unsupported / can't verify, always with a verbatim quote.
4. **Prove it** — click a claim, see the sentence highlighted in the source, side by side.
5. **Study mode** — quiz questions generated *only* from verified claim+quote pairs.

**The rule that makes it trustworthy:** the verifier must return a verbatim quote or abstain.
Every returned quote is string-matched against the extracted page text; anything that doesn't
match is downgraded to *can't verify*. The model cannot invent support.

## Quickstart

```bash
cd backend
python -m venv .venv && .venv\Scripts\activate      # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Then open `frontend/index.html` in a browser. With `MOCK=1` (the default in `.env.example`)
the API returns the labels in `data/answer_key.json`, so the UI is demoable before the
verifier exists.

Fetch the test PDFs (they are not committed):

```bash
python scripts/fetch_sources.py
```

## Repo map

| Path | What's in it |
|---|---|
| `data/essay_draft.md` | Synthetic 12-claim essay with 3 planted citation errors |
| `data/answer_key.json` | Ground truth for those 12 claims (this is the A3 evaluation) |
| `data/sources/` | Where the two arXiv PDFs land (gitignored) |
| `prompts/` | Claim extraction, verification, quiz prompts |
| `backend/app/` | FastAPI skeleton: models, PDF extraction, quote-matching |
| `frontend/index.html` | Single-file UI, no build step |
| `eval/run_eval.py` | Scores the app against the answer key, writes `eval/results.md` |
| `EVIDENCE.md` | Rubric evidence tables — **fill this in as you go** |
| `docs/PLAN.md` | Roles, 72-hour plan, cut list |
| `docs/DEMO_SCRIPT.md` | Beat-by-beat video script |
| `docs/SUBMISSION.md` | The five Devpost answers, as prompts to fill |

## Rubric map

| Rubric | Where the evidence lives |
|---|---|
| V1, V2, V3 | `EVIDENCE.md` §V |
| A1, A2 | `EVIDENCE.md` §A + `backend/app/verify.py` |
| A3 | `eval/results.md` + `data/answer_key.json` |
| A4 | `EVIDENCE.md` §A4 log (start it today) |
| R1, R2 | `docs/DEMO_SCRIPT.md` + `EVIDENCE.md` §R2 |
| R3 | `EVIDENCE.md` §R3 |
| D1–D4 | `frontend/index.html` + `EVIDENCE.md` §D |

## Scope

**In:** essay + sources → verdicts with quotes → study mode.
**Out (say so in limitations):** accounts, collaboration, `.docx` export, handwriting OCR,
multi-language, browser extension, live URL crawling.

## Sources

Both test papers are open-access on arXiv:

- `2307.03172` — Liu et al., *Lost in the Middle: How Language Models Use Long Contexts*
- `2305.14627` — Gao et al., *Enabling Large Language Models to Generate Text with Citations*

Do not commit third-party PDFs. `scripts/fetch_sources.py` downloads them locally; check each
paper's license before redistributing.
