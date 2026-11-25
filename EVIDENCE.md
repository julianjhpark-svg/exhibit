# Evidence pack

Judges score from the video and the Devpost description. They do **not** run the project.
Fill this in as you go — on Saturday it becomes the description, and every row here is points.

Rubric labels are the event's own; judges look for them. Keep the numbers honest.

---

## V — Problem Value & Practicality (20)

### V1 — real need (8)

| | Evidence |
|---|---|
| Who | <e.g. second-year students writing 3+ cited essays per term> |
| Specific situation | <e.g. pasting AI-drafted paragraphs and having to trust the citations> |
| Evidence of need | <a quote from a classmate/TA, a firsthand account, or a published source + link> |
| Use example | <"Maya pastes her 1,200-word draft and two PDFs; 12 claims are checked in ~40s; 2 are flagged before submission"> |

> Keep the user tiny and specific. "Students" is not a user; "first-year students in a
> required writing seminar" is.

### V2 — supported advantage (8)

Compare against the **manual** method (Ctrl-F each citation) and **one existing tool**. Measure it.

| | Manual (Ctrl-F) | ChatGPT/Claude prompt | Exhibit |
|---|---|---|---|
| Steps per claim | | | |
| Time for 12 claims | <measure it, actually> | | |
| Gives a page-anchored quote? | | | |
| Admits when nothing supports the claim? | | | |
| Cost | | | |

Source of the numbers: <"we timed ourselves on 12 claims on 27 Nov", or a cited capability page>.

**The advantage in one sentence:** <e.g. "manual checking takes 14 minutes and still misses the
misattributed claim; Exhibit takes 40 seconds and refuses to guess">

### V3 — could they actually use it (4)

<Free tier, browser only, no account, works on a laptop, PDFs stay local. State the one
requirement that could block someone (an API key? internet?) and how they'd meet it.>

---

## A — AI Integration & Development (30)

### A1 — justified AI choice (6)

| | |
|---|---|
| Model / method | <e.g. gpt-5-mini for verification; regex + string match for the quote check> |
| Why this one | <cost per claim, speed, structured-output reliability, or "runs on the user's key"> |
| Evidence it matters | <official pricing/context page, or our own test: same 12 claims on 2 models, table below> |

| Model | Verdict accuracy | Fabricated quotes | Cost / 12 claims | p50 latency |
|---|---|---|---|---|
| | | | | |
| | | | | |

### A2 — the project-specific AI decision (10)

**The decision:** quote-or-abstain + a deterministic string match.

1. The verifier may only mark a claim `supported` by returning a **contiguous verbatim span**.
2. `backend/app/verify.py::enforce()` checks that span against the extracted page text.
3. Any mismatch is downgraded to `can't verify`, with the reason shown to the user.

**Why it helps:** <the model's fluency stops being trusted; support becomes a fact about a string>.
**Evidence:** <"on 12 claims, X of Y returned quotes matched verbatim; the 2 mismatches were
downgraded, and without the check they would have been accepted as support">.

<Optional second decision if you have time: quote-first vs verdict-first prompting. Pick the
winner by measured fabricated-quote rate, and say so in one sentence.>

### A3 — checked AI quality and limits (8)

Method: `data/answer_key.json` holds 12 hand-labelled claims (7 supported, 2 partial, 2
unsupported, 1 unverifiable). Run `python eval/run_eval.py` after every prompt change.

| Metric | Result |
|---|---|
| Verdict accuracy | <x/12> |
| Over-credulity (partial/unsupported called supported) | <n> |
| Abstention on unsupported claims | <n/3> |
| Quote fidelity (verbatim match) | <n/n> |

**Where it can be relied on:** <clean text-layer PDFs, expository prose, claims that map to 1–2
sentences>.
**Where it cannot:** <tables/figures, scanned pages, claims needing synthesis across 3+ sources,
claims whose support is spread over two paragraphs — our C__ case>.
**One weakness we found and did not hide:** <e.g. it marks an overstatement "partial" instead of
"unsupported" when the qualifier is dropped>.

### A4 — AI-assisted development, checked (6)

| # | What AI produced | How a human checked it | What the check found | Kept / changed / rejected |
|---|---|---|---|---|
| 1 | `extract.py` PDF chunker | ran it on both test PDFs, compared chunk count + eyeballed page 3 | lost the last paragraph of each page | **changed** — chunker now carries a tail |
| 2 | <claim-extraction prompt> | <ran on essay_draft, compared to answer_key> | <split C09 at the nested quote> | <changed> |
| 3 | | | | |

> This table is worth 6 points and takes 15 minutes. Fill it in on Friday, from real events.

---

## R — Functionality & Reliability (30)

### R1 — the complete main process (6)

Start action → result, in one unbroken take in the video:
`paste essay → add 2 PDFs → check → 12 verdicts → click the fabricated claim → source highlight`

Manual steps to disclose honestly: <e.g. "claims are extracted automatically; the verifier runs
once per claim, ~3s each, so a 12-claim check takes ~40s">

### R2 — correct across situations (16)

| Case | What should happen | What happened | Evidence |
|---|---|---|---|
| Ordinary 1 — planted-error essay | 7 supported, 2 partial, 2 unsupported, 1 can't verify | | video 0:35 |
| Ordinary 2 — a real essay on the same 2 papers | verdicts match a hand check | | screenshot |
| Repeat of #1 | identical verdicts (temperature 0 + cached calls) | | table |
| Demanding — 40-page PDF, claim split across two pages | finds the passage, correct page | | video 1:20 |

### R3 — failures handled (8)

| Failure | Cause | Detected how | What the user sees | Prior work preserved? |
|---|---|---|---|---|
| Scanned PDF | data | median chars/page < 200 in `extract.py` | "no text layer" + paste-it-instead hint | yes, other sources stay loaded |
| Fabricated quote from the model | model result | `verify.is_verbatim()` | downgraded to can't verify, reason shown | yes, other verdicts kept |
| Provider timeout / spend cap (Prune) | service | request timeout / 429 | retry once, then "not checked" for the rest | yes, results persist |

> Two *different causes* is the requirement. One data, one model-or-service is the safest pair.

---

## D — Design Quality & UX (20)

**D1 — primary action stands out (4):** <one input action, one result band (the counts), details
collapsed. Say what you removed.>

**D2 — coherent, finished (4):** <one token set in `frontend/index.html`; identical chips, spacing,
and empty/error states. Screenshot the empty state — most teams forget it.>

**D3 — removed user effort (4):** <"Only problems" filter, jump-to-exhibit, batch check — instead
of scrolling 40 pages per claim. Before/after in the video.>

**D4 — findable + relationship visible (8):** <claim list grouped by verdict; clicking a claim
highlights the exact span in the source beside it. This is the 5-point checkbox — show it clearly.>

---

## Pre-submit checklist

- [ ] Public repo, no `.env`, no PDFs, no API keys (`git log -p | grep -i "sk-"` is worth running)
- [ ] README quickstart works from a clean clone
- [ ] Video 2–4 min, embedded, plays logged out, YouTube/Vimeo
- [ ] All 4 teammates on the Devpost roster
- [ ] Every teammate submitted the participant form
- [ ] AI disclosure names the model(s) and what each did
- [ ] Prune named if used, and Best Use of Prune selected if you want that award
- [ ] Limitations section names every simulated/unfinished part
