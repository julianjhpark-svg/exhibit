# Runbook

Executable steps from "scaffold" to "submitted". Follow in order; each step has a **done when**
you can check in ten seconds. Estimates assume one person per role (see `docs/PLAN.md`).

Deadline: **Sat 28 Nov, 3:00 pm PST**. Plan to submit at **1:00 pm PST**.

---

## Step 0 — Everyone, 10 minutes

```powershell
cd C:\Users\SAMSUNG\OneDrive\Documents\Hackathon\exhibit
python scripts/fetch_sources.py
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Open `frontend/index.html`. You should see 5 claims and a highlight. Then:

```powershell
python eval\run_eval.py --mock
```

**Done when:** 12/12, and both PDFs are in `data/sources/`.

> If either PDF fails to download, get it from arxiv.org manually and rename it
> `2307.03172.pdf` / `2305.14627.pdf`.

---

## Step 1 — Model client (B, 45 min)

Create `backend/app/llm.py`: one function, no SDK.

```python
async def chat_json(system: str, user: str, *, timeout: float = 45) -> dict
```

- POST to `{LLM_BASE_URL}/chat/completions` with `httpx.AsyncClient`.
- `temperature=0` (required for the R2 repeat check).
- `response_format={"type": "json_object"}` if supported; otherwise strip ```` ```json ```` fences
  before `json.loads`.
- Raise `ProviderTimeout` / `ProviderRateLimited` on 408/429/5xx — step 9 needs these types.
- `.env`: `LLM_BASE_URL` (default `https://api.openai.com/v1`), `LLM_API_KEY`, `MODEL`.
  For Prune, change **only** `LLM_BASE_URL` and `LLM_API_KEY`.

**Done when:** a one-off call returns parsed JSON, and a bogus base URL raises `ProviderTimeout`
in under 5 seconds.

---

## Step 2 — Claim extraction (B, 2 h) ⚠️ highest risk

Create `backend/app/claims.py` and use `prompts/claim_extraction.md` verbatim as the system prompt.

```python
async def extract_claims(essay: str, max_claims: int = 30) -> list[Claim]
```

- Fallback: if the model call fails, use the sentence splitter already in `main.py` — a degraded
  demo beats a dead one, and it's failure #3 if you want it.
- Add `python -m app.claims` as a CLI: reads `data/essay_draft.md`, prints the claim count and any
  claim whose text doesn't match the answer key.

**Done when:** 12 claims, and all 12 match `answer_key.json` after whitespace/case normalisation.

> This is the step that decides your accuracy score. Sanity-check by eyeball first: the sentence
> with nested quotes (C09) is the one that usually gets mangled.

---

## Step 3 — Retrieval (B, 1–2 h)

Add `rank_bm25==0.2.2` to `backend/requirements.txt`. Create `backend/app/retrieve.py`.

```python
def build_index(sources: list[Source]) -> Index          # chunks via extract.passages_from()
def top_k(index, claim: str, k: int = 8) -> list[Passage]
```

- Index is per-request (two papers, ~200 chunks) — no vector DB, no embeddings. Lexical is enough
  and it keeps the demo offline-safe.
- Print **retrieval recall**: for each of the 12 claims, is the gold source's page in the top 8?

**Done when:** recall ≥ 10/12 on the answer key, and C04's abstract sentence appears for C04.

> If recall is poor, chunk by paragraph instead of 900 characters. Do not add embeddings — you
> don't have the hours.

---

## Step 4 — Verifier + guard (B, 2 h) ⚠️ the product

Create `backend/app/verifier.py`.

```python
async def verify(claim: Claim, passages: list[Passage]) -> VerdictOut
```

1. System prompt: `prompts/verification.md`, verbatim.
2. User message: the claim + passages as `[1] source_id p.3: text`.
3. Parse JSON → `VerdictOut`.
4. **Count, before enforcing:** `raw_quotes_ok` = how many returned quotes are already verbatim.
   This number is your A2 evidence (the guard's contribution) — keep it in the run stats.
5. `enforce(verdict, page_text)` using the cited page's extracted text.
6. If the model throws, return `cant_verify` with `reason="provider error"` — never fabricate.

**Done when:** on the sample essay, **C10 comes back `unsupported` with `quote: null`**, and C04
comes back `supported` with a quote found verbatim in page 1.

---

## Step 5 — Wire `/api/check` (B, 1 h)

In `main.py`, replace the `if MOCK:` branch with: extract → retrieve → verify (bounded
`asyncio.gather`, max 4 concurrent) → tally.

Add to each `VerdictOut` the cited page's text (`page_text`) so the frontend can highlight without
a second request. Trim it to ±600 chars around the quote.

**Done when:**

```powershell
curl -X POST localhost:8000/api/check -H "Content-Type: application/json" ^
  -d "{\"essay\":\"<paste essay>\",\"sources\":[{\"id\":\"liu2023\",\"title\":\"x\"}]}"
```

returns 12 verdicts, `stats.total == 12`, and finishes in under 60 s.

---

## Step 6 — Frontend live (C, 3 h)

In `frontend/index.html`, delete the sample `STATE.claims` fallback only after the live path works.

1. `POST /api/check` on "Check" click; show a skeleton while waiting.
2. Render chips from `verdict`; counts from `stats`.
3. On claim click, highlight `quote` inside `page_text`. **Use the page text, not `PAGE.text`.**
   If the quote isn't found, show the page without a highlight and a small "not found on this page"
   note — that's honest, and it's a real bug signal during dev.
4. Keep the "Only problems" filter.

**Done when:** a full run renders 12 claims, and clicking C04 highlights a sentence.

> Gotcha: PDF text and model quotes differ in quotes/dashes/hyphens. Highlight with a
> whitespace-flexible case-insensitive search, not `indexOf` on raw strings.

---

## Step 7 — States (C, 1.5 h)

- Loading: 12 skeleton rows, not a spinner.
- Empty: "Add a source to start" with the file picker focused.
- Error: banner with the exact reason + a retry button.
- Per-claim failure: chip stays `can't verify` with `reason` visible.

**Done when:** you can screenshot all four states. D2 and R3 both score off these.

---

## Step 8 — Failure #1: scanned PDF (A, 1 h)

Make the fixture: open one PDF, print page 2 to an image, save as `scanned_test.pdf`
(**do not commit it**; keep it in `runs/`, which is gitignored).

- POST it to `/api/sources` → expect 422 `no_text_layer`.
- In the UI: red banner, existing sources still listed, editor still usable.

**Done when:** screenshot shows the refusal *and* the previously loaded source still working.

---

## Step 9 — Failure #2: provider (A, 1.5 h)

Set `LLM_BASE_URL=http://127.0.0.1:9/v1` (nothing listening) or a 1 ms timeout.

- Retry once, then mark the remaining claims `cant_verify` with `reason="provider unavailable"`.
- Prior verdicts must survive; the run must not crash or blank the page.
- Restore config and confirm the next run works.

**Done when:** screenshot of the degraded run + a successful run afterwards. Two *different causes*
(step 8 data, step 9 service) satisfies R3.

---

## Step 10 — Evaluation (D, 1 h)

```powershell
cd exhibit
python eval\run_eval.py
```

Paste into `EVIDENCE.md` §A3 and `docs/SUBMISSION.md`:

- verdict accuracy `n/12`
- over-credulity (partial/unsupported called supported)
- quote fidelity **before** the guard (`raw_quotes_ok / 12`) and after (should be 12/12)
- downgrades count
- retrieval recall from step 3

Then write two sentences: what it's reliable for, and the specific case it fails on.

**Done when:** `eval/results.md` has real numbers and no `MOCK` in the header.

---

## Step 11 — Prune (A, 1 h, optional but best prize odds)

1. Sign up through the event link, get the key.
2. `LLM_BASE_URL=<prune url>`, `LLM_API_KEY=<prune key>`, remove the provider key from `.env`.
3. Re-run step 10. Same verdicts, lower cost.
4. Screenshot the spend/cost view. One sentence in the description; tick **Best Use of Prune**.

**Done when:** step 10 passes through Prune, and you have the screenshot.

---

## Step 12 — Demo video (D + all, 3 h)

Follow `docs/DEMO_SCRIPT.md` beat by beat. Record Friday evening even if it's rough; re-record
Saturday morning.

**Done when:** 2–4 min, embedded, plays in a private window, shows C10 being caught.

---

## Step 13 — Submit (D, 2 h)

1. `EVIDENCE.md` and `docs/SUBMISSION.md`: every `<...>` filled.
2. README quickstart matches reality (test it in a fresh clone if you can).
3. `git log -p | Select-String "sk-"` → must return nothing. No `.env`, no PDFs committed.
4. Devpost: repo, video, five answers, full roster.
5. Every teammate submits the participant form.
6. Submit at **1:00 pm PST**.

---

## Order if you fall behind

Keep: 2, 3, 4, 5, 10, 12. Cut: 7 (states), 11 (Prune), 6's polish, Study Mode.
Never cut: **C10 caught**, **two failures**, **the eval table**, **the video**.
