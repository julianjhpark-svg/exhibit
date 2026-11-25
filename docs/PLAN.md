# Plan — 4 people, 3 days

Deadline: **Sat 28 Nov, 3:00 pm PST**. Treat the real deadline as **1:00 pm PST**.
Code freeze: **Sat 09:00 am PST**.

## Roles

You all "can do everything", so the split is about *ownership*, not skill.

| Person | Owns | Done means |
|---|---|---|
| **A** | Ingestion + reliability: PDF page extraction, no-text-layer detection, persistence, timeout/spend-cap paths | A bad file can't crash the app, and every failure has a screenshot |
| **B** | Verifier: claim extraction, retrieval, quote-or-abstain prompt, `verify.enforce()` | 12/12 claims return a verdict, and fabricated quotes get downgraded |
| **C** | Frontend: the five screens, highlight pane, filter, empty/error states | Someone can use it without being told what to click |
| **D** | Eval + evidence: answer key, `eval/results.md`, `EVIDENCE.md`, A4 log, video, Devpost text | Every table in `EVIDENCE.md` has real numbers by Friday night |

D is not a spare pair of hands. D is worth ~20 points nobody else will collect.

## Day by day

**Wed 25 (today, half day)**
- [ ] Freeze the name: **Exhibit**. Buy nothing.
- [ ] `git init`, first commit, push to GitHub (public).
- [ ] A: `extract_pages()` works on both PDFs, page numbers correct.
- [ ] B: one claim verified by hand end-to-end (CLI is fine) — C10 must come back unsupported.
- [ ] D: confirm the 12-claim answer key, start the A4 log, time the manual Ctrl-F baseline (V2).
- [ ] C: `frontend/index.html` open in a browser, sample data rendering.

**Thu 26**
- [ ] B: real `/api/check` — extraction → retrieval → verify → enforce → tally. `MOCK=0`.
- [ ] A: upload endpoint + both failure paths (scanned PDF, oversized file).
- [ ] C: wire the UI to the live API, verdict chips, source pane with highlight.
- [ ] D: first `eval/results.md` by 20:00. Report accuracy out loud to the team.

**Fri 27**
- [ ] B: fix the worst error the eval exposed. Only one — write down what you rejected.
- [ ] A: timeout / spend-cap failure (Prune), persistence so failures don't wipe the session.
- [ ] C: empty state, loading state, error state, "only problems" filter, study mode.
- [ ] D: fill `EVIDENCE.md` §V/§A/§R/§D with real numbers; draft the Devpost answers.
- [ ] All: record a rough demo at 18:00. Watch it. Cut whatever is confusing.

**Sat 28**
- [ ] 09:00 code freeze. No new features. Only copy, screenshots, video.
- [ ] 10:00 final video recorded (2–4 min, one take per beat).
- [ ] 11:00 Devpost description pasted, links checked logged-out.
- [ ] 12:00 submit. 13:00 at the absolute latest.

## Cut list (in order)

1. Study mode (keep the endpoint stub, say it's planned)
2. URL sources (PDF + paste only)
3. Embeddings/hybrid retrieval (lexical only)
4. Multiple sources per claim

**Never cut:** the fabricated-claim case, the two failure demos, the eval table, the highlight pane.

## Risks

| Risk | Likelihood | Move |
|---|---|---|
| Claim extraction splits sentences differently from the answer key | high | match by normalised text, and adjust the key, not the essay |
| Retrieval misses the right page on the 40-page PDF | medium | chunk per paragraph, top-k=8, and show the retrieved pages in the UI as a fallback |
| Model returns a paraphrase instead of a quote | medium | `enforce()` already handles it — that's the story, not a bug |
| Team runs out of time on the video | high | D records beat-by-beat on Friday; the video is not a Saturday task |
| Someone commits `.env` or a PDF | medium | check `.gitignore` before the first push; scan before submitting |

## Definition of done

1. A stranger can paste the sample essay, add two PDFs, and get 12 verdicts with quotes.
2. The planted 98.1% claim is caught on camera.
3. `eval/results.md` has real numbers and one honest limitation.
4. `EVIDENCE.md` has no `<...>` placeholders left.
5. The video plays in a private browser window.
